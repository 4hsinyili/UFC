const today = moment();
const startDateDom = document.querySelector('#start-date')
const endDateDom = document.querySelector('#end-date')
const startTimeDom = document.querySelector('#start-time')
const endTimeDom = document.querySelector('#end-time')
const todayDate = today.format('YYYY-MM-DD')
const nowTime = today.format('HH:mm')
const utcOffset = moment().utcOffset()
const utcNow = moment().utcOffset(-(utcOffset))
const todayStartRefresh = moment().set({'hour': 2 + (utcOffset /60), 'minutes': 30, 'second': 0}).utcOffset(-(utcOffset))
const todayEndRefresh = moment().set({'hour': 3 + (utcOffset /60), 'minutes': 10, 'second': 0}).utcOffset(-(utcOffset))

const weekAgo = moment().subtract(7, 'days');
let initMoment = today
if (weekAgo.isAfter(moment('2021-06-21'))){
    initMoment = weekAgo
} else {
    initMoment = moment('2021-06-21')
}

const initDate = initMoment.format('YYYY-MM-DD')

startDateDom.value = initDate
endDateDom.value = todayDate
startDateDom.min = '2021-06-21'
startDateDom.max = todayDate
endDateDom.min = '2021-06-21'
endDateDom.max = todayDate
startTimeDom.value = '00:00'
endTimeDom.value = nowTime

const initData = {"start_date_time": `${initDate} ${startTimeDom.value}`, "end_date_time": `${todayDate} ${endTimeDom.value}`}

const ueLambdaDinerCountGraph = document.getElementById('ue-lambda-bar-graph');
const fpLambdaDinerCountGraph = document.getElementById('fp-lambda-bar-graph');
const lambdaRuntimeGraph = document.getElementById('lambda-line-graph');
const mDinerCountGraph = document.getElementById('m-bar-graph');
const pDinerCountGraph = document.getElementById('p-bar-graph');
const mpRunTimeGraph = document.getElementById('mp-line-graph');
const dashboardApi = 'api/v1/dashboard';

const csrftoken = getCookie('csrftoken');


function initPost(dashboardApi, intData){
    resetTableS()
    resetGraphS()
    showLoading()
    ajaxPost(dashboardApi, intData, function(response){
        renderDashBoard(response)
        endLoading()
    })
}

const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 1200,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.addEventListener('mouseenter', Swal.stopTimer)
      toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
  })

function autoUpadte(){
    let startDate = startDateDom.value
    let endDate = endDateDom.value
    let startTime = startTimeDom.value
    let endTime = endTimeDom.value
    let data = {"start_date_time": `${startDate} ${startTime}`, "end_date_time": `${endDate} ${endTime}`}
    ajaxPost(dashboardApi, data, function(response){
        resetTableS()
        renderDashBoard(response)
        Toast.fire({
            icon: 'success',
            title: '資料更新'
          })
    })
}

function renderDashBoard(response){
    
    let data = response.data
    try{
        let ueListStartData = data.get_ue_list_start
        let ueListData = data.get_ue_list
        let ueDetailData = data.get_ue_detail
        dispatchLambdaData(ueListStartData, ueListData, ueDetailData, 'ue')
    } catch(error){
        graphError('ue-lambda-bar')
        graphError('ue-lambda-line')
    }

    try{
        let fpListStartData = data.get_fp_list_start
        let fpListData = data.get_fp_list
        let fpDetailData = data.get_fp_detail
        dispatchLambdaData(fpListStartData, fpListData, fpDetailData, 'fp')
    } catch(error){
        graphError('fp-lambda-bar')
        graphError('fp-lambda-line')
    }
    
    try{
        let matchStartData = data.match_start
        let matchData = data.match
        dispatchMatchData(matchStartData, matchData, 'match')
    } catch(error){
        graphError('match-bar')
        graphError('match-line')
    }

    try{
        let placeStartData = data.place_start
        let placeData = data.place
        dispatchPlaceData(placeStartData, placeData, 'place')
    } catch(error){
        graphError('place-bar')
        graphError('place-line')
    }
}

function errorTest(){
    graphError('ue-lambda-bar')
    graphError('ue-lambda-line')
    graphError('fp-lambda-bar')
    graphError('fp-lambda-line')
    graphError('match-bar')
    graphError('match-line')
    graphError('place-bar')
    graphError('place-line')
}


function dispatchLambdaData(listStartData, listData, detailData, source){
    let batchIds = Object.keys(listStartData)
    batchIds = batchIds.sort()
    listBarInfo = new Array()
    detailBarInfo = new Array()
    listLineInfo = new Array()
    detailLineInfo = new Array()
    graphXArray = new Array()
    for (let i=0; i<batchIds.length; i ++){
        let batchId = batchIds[i]
        let startData = listStartData[batchId]
        let runData = false
        try {
            runData = listData[batchId]
        } catch (error) {
        }
        let detailSlice = detailData[batchId]
        listInfo = renderList(startData, runData, source.concat('-list'))
        if (listInfo){
            detailInfo = renderDetail(listInfo, detailSlice, source.concat('-detail'))
            if (detailInfo){
                let graphX = batchId
                graphX = moment.unix(graphX).toDate()
                graphXArray.push(graphX)
                listBarInfo.push(listInfo.diner_count)
                detailBarInfo.push(detailInfo.diner_count)
                listLineInfo.push(listInfo.run_time)
                detailLineInfo.push(detailInfo.run_time)
            }
        }   
    }
    if (graphXArray.length > 0){
        renderLambdaDinerCountGraph([graphXArray, listBarInfo, detailBarInfo], source)
        renderLambdaRunTimeGraph([graphXArray, listLineInfo, detailLineInfo], source)
    }
    document.querySelector('[name="lambda-table"]').classList = 'table table-hover table-striped'
}

function dispatchMatchData(matchStartData, matchData, source){
    let batchIds = Object.keys(matchStartData)
    batchIds = batchIds.sort()
    barInfoDC = new Array()
    barInfoMC = new Array()
    lineInfo = new Array()
    graphXArray = new Array()
    for (let i=0; i<batchIds.length; i ++){
        let batchId = batchIds[i]
        let startData = matchStartData[batchId]
        let runData = false
        try {
            runData = matchData[batchId]
        } catch (error) {
        }
        info = renderMatch(startData, runData, source)
        if (info){
            graphXArray.push(info.x.toDate())
            barInfoDC.push(info.unmatch_count)
            barInfoMC.push(info.match_count)
            lineInfo.push(info.run_time)
        }
    }
    if (graphXArray.length > 0){
        renderMDinerCountGraph([graphXArray, barInfoMC, barInfoDC], source)
        renderMRunTimeGraph([graphXArray, lineInfo], source)
    }
}

function dispatchPlaceData(placeStartData, placeData, source){
    let batchIds = Object.keys(placeStartData)
    batchIds = batchIds.sort()
    barInfoAFC = new Array()
    barInfoANFC = new Array()
    barInfoUFC = new Array()
    barInfoUNFC = new Array()
    lineInfo = new Array()
    graphXArray = new Array()
    for (let i=0; i<batchIds.length; i ++){
        let batchId = batchIds[i]
        let startData = placeStartData[batchId]
        let runData = false
        try {
            runData = placeData[batchId]
        } catch (error) {
        }
        info = renderPlace(startData, runData, source)
        if (info){
            graphXArray.push(info.x.toDate())
            barInfoAFC.push(info.api_found)
            barInfoANFC.push(info.api_not_found)
            barInfoUFC.push(info.update_found_count)
            barInfoUNFC.push(info.update_not_found_count)
            lineInfo.push(info.run_time)
        }
    }
    if (graphXArray.length > 0){
        renderPDinerCountGraph([graphXArray, barInfoAFC, barInfoANFC, barInfoUFC, barInfoUNFC], source)
        renderPRunTimeGraph([graphXArray, lineInfo], source)
    }
}

function appendRow(tableName, rowType, info){
    let tableBody = document.querySelector(`[name="${tableName}-body"]`)
    let firstRow = tableBody.querySelector(`[name="${tableName}-${rowType}-row"]`)
    let allRows = tableBody.querySelectorAll(`[name="${tableName}-${rowType}-row"]`)
    let lastRow = tableBody.querySelector(`[name="${tableName}-${rowType}-row"][data-number="${allRows.length - 1}"]`)
    let newRow = firstRow.cloneNode(true)
    newRow.setAttribute('data-number', allRows.length)
    if (tableName == 'lambda-table'){newRow = renderLambdaRow(newRow, info)}
    else if (tableName == 'match-table'){newRow = renderMatchRow(newRow, info)}
    else if (tableName == 'place-table'){newRow = renderPlaceRow(newRow, info)}
    $(newRow).insertAfter(lastRow)
    $(newRow).show()
    return newRow
}

function renderLambdaRow(row, info){
    row.querySelector(`[data-cell="log-time"]`).innerText = info.start_time
    row.querySelector(`[data-cell="branches-count"]`).innerText = info.branches_count
    row.querySelector(`[data-cell="diner-count"]`).innerText = info.diner_count
    row.querySelector(`[data-cell="run-time"]`).innerText = info.run_time
    return row
}

function renderMatchRow(row, info){
    row.querySelector(`[data-cell="log-time"]`).innerText = info.start_time
    row.querySelector(`[data-cell="match-count"]`).innerText = info.match_count
    row.querySelector(`[data-cell="diner-count"]`).innerText = info.diner_count
    row.querySelector(`[data-cell="run-time"]`).innerText = info.run_time
    return row
}

function renderPlaceRow(row, info){
    row.querySelector(`[data-cell="log-time"]`).innerText = info.start_time
    row.querySelector(`[data-cell="update-found-count"]`).innerText = info.update_found_count
    row.querySelector(`[data-cell="update-not-found-count"]`).innerText = info.update_not_found_count
    row.querySelector(`[data-cell="api-found-count"]`).innerText = info.api_found
    row.querySelector(`[data-cell="api-not-found-count"]`).innerText = info.api_not_found
    row.querySelector(`[data-cell="run-time"]`).innerText = info.run_time
    return row
}

function sumData(arr){
    var sum=0;
    for (var i = 0; i < arr.length; i++) {
        sum += arr[i];
    };
    return sum;
}

function renderList(listStartData, listData, rowType){
    if ((!listStartData) || (!listData)){
        return false
    }
    if (listStartData.length != listData.length){
        return false
    }
    let branchesCount = listData.length
    let dinerCountArray = new Array()
    let startTimeArray = new Array()
    let endTimeArray = new Array()
    for (let i=0; i<listStartData.length; i++){
        let startData = listStartData[i]
        let startTime = moment(startData.log_time).add(8, 'hours');
        startTimeArray.push(startTime)
        }
    for (let i=0; i<listData.length; i++){
        let runData = listData[i]
        let endTime = moment(runData.log_time).add(8, 'hours');
        let dinerCount = runData.records_count
        dinerCountArray.push(dinerCount)
        endTimeArray.push(endTime)
        }
    let dinerCountTotal = sumData(dinerCountArray)
    let startTimeMin = moment.min(startTimeArray)
    let endTimeMax = moment.max(endTimeArray)
    let runTimeMax = moment.duration(endTimeMax.diff(startTimeMin)).asMilliseconds() / 1000 / branchesCount
    startTimeMin = startTimeMin.format('YYYY-MM-DD HH:mm:ss')
    endTimeMax = endTimeMax.format('YYYY-MM-DD HH:mm:ss')
    let info = {
        'branches_count': branchesCount,
        'run_time': runTimeMax,
        'diner_count': dinerCountTotal,
        'start_time': startTimeMin,
        'end_time': endTimeMax
    }
    appendRow('lambda-table', rowType, info)
    return info
}

function renderDetail(listInfo, detailData, rowType){
    if ((!listInfo) || (!detailData)){
        return false
    }
    let branchesCount = detailData.length
    let runTimeArray = new Array()
    let dinerCountArray = new Array()
    let startTime = listInfo.end_time
    let endTimeArray = new Array()
    for (let i=0; i<detailData.length; i++){
        let runData = detailData[i]
        let endTime = moment(runData.log_time).add(8, 'hours');
        let runTime = moment.duration(endTime.diff(startTime)).asMilliseconds() / 1000
        let dinerCount = runData.records_count
        runTimeArray.push(runTime)
        dinerCountArray.push(dinerCount)
        endTimeArray.push(endTime)
        }
    let runTimeAvg = sumData(runTimeArray) / runTimeArray.length
    let dinerCountTotal = sumData(dinerCountArray)
    let endTimeMax = moment.max(endTimeArray).format('YYYY-MM-DD HH:mm:ss')
    let info = {
        'branches_count': branchesCount,
        'run_time': runTimeAvg,
        'diner_count': dinerCountTotal,
        'start_time': startTime,
        'end_time': endTimeMax
    }
    appendRow('lambda-table', rowType, info)
    return info
}

function renderMatch(matchStartData, matchData, rowType){
    if ((!matchStartData) || (!matchData)){
        return false
    }
    let startData = matchStartData[matchStartData.length - 1]
    let runData = matchData[matchData.length -1]
    let startTime = moment(startData.log_time).add(8, 'hours');
    let endTime = moment(runData.log_time).add(8, 'hours');
    let runTime = moment.duration(endTime.diff(startTime)).asMilliseconds() / 1000
    let dinerCount = runData.records_count
    let matchCount = runData.matched_count
    let info = {
        'run_time': runTime,
        'diner_count': dinerCount,
        'unmatch_count': dinerCount - matchCount,
        'match_count': matchCount,
        'start_time': startTime.format('YYYY-MM-DD HH:mm:ss'),
        'end_time': endTime.format('YYYY-MM-DD HH:mm:ss'),
        'x': startTime
    }
    appendRow('match-table', rowType, info)
    return info
}

function renderPlace(placeStartData, placeData, rowType){
    if ((!placeStartData) || (!placeData)){
        return false
    }
    let startData = placeStartData[placeStartData.length -1]
    let runData = placeData[placeData.length -1]
    let startTime = moment(startData.log_time).add(8, 'hours');
    let endTime = moment(runData.log_time).add(8, 'hours');
    let runTime = moment.duration(endTime.diff(startTime)).asMilliseconds() / 1000
    let updateFoundCount = runData.update_found_count
    let updateNotFoundCount = runData.update_not_found_count
    let apiFoundCount = runData.api_found
    let apiNotFoundCount = runData.api_not_found
    let info = {
        'run_time': runTime,
        'update_found_count': updateFoundCount,
        'update_not_found_count': updateNotFoundCount,
        'api_found': apiFoundCount,
        'api_not_found': apiNotFoundCount,
        'start_time': startTime.format('YYYY-MM-DD HH:mm:ss'),
        'end_time': endTime.format('YYYY-MM-DD HH:mm:ss'),
        'x': startTime
    }
    appendRow('place-table', rowType, info)
    return info
}

function resetTableS(){
    let rows = document.querySelectorAll('[data-number]:not([data-number="0"])')
    for (let i=0; i < rows.length; i++){
        rows[i].remove()
    }
}

function resetGraphS(){
    resetGraph('ue-lambda-bar')
    resetGraph('ue-lambda-line')
    resetGraph('fp-lambda-bar')
    resetGraph('fp-lambda-line')
    resetGraph('match-bar')
    resetGraph('match-line')
    resetGraph('place-bar')
    resetGraph('place-line')
}

function resetGraph(graphId){
    document.getElementById(graphId.concat('-graph')).setAttribute('data-show', 'yes')
    document.getElementById(graphId.concat('-404')).setAttribute('data-show', 'no')
}

function graphError(graphId){
    document.getElementById(graphId.concat('-graph')).setAttribute('data-show', 'no')
    document.getElementById(graphId.concat('-404')).setAttribute('data-show', 'yes')
}

function renderLambdaDinerCountGraph(infoArray, source){
    let x = infoArray[0]
    let listDinerCount = infoArray[1]
    let detailDinerCount = infoArray[2]
    let plotConf = [
        {
            y: listDinerCount,
            x: x,
            type: "bar",
            name: "遍歷候選餐廳總數",
            marker: {
                color: '#5999d4',
                opacity: 0.8,
              }
          },
          {
            y: detailDinerCount,
            x: x,
            type: "bar",
            name: "可外送到 Appworks School 餐廳數",
            marker: {
                color: '#003585',
                opacity: 0.8,
              }
          }
    ]
    let plotTitle = ''
    if (source == 'ue'){plotTitle = 'Uber Eats 爬取餐廳數量'}
    else {plotTitle = 'Food Panda 爬取餐廳數量'}
    let layout = {
        title: {
            text: plotTitle,
            font: {
              size: 18
            },
            x: 0.15,
            y: 0.985
          },
        legend: {
            "orientation": "h",
            "y" : 1.16
        },
        margin: {
            t: 70,
            b: 70
        }
    }
    let graph = document.getElementById(source.concat('-lambda-bar-graph'))
    Plotly.newPlot( graph, plotConf, layout);
}

function renderLambdaRunTimeGraph(infoArray, source){
    let x = infoArray[0]
    let listRunTime = infoArray[1]
    let detailRunTime = infoArray[2]
    let trace1 = {
        x: x,
        y: listRunTime,
        name: '遍歷候選餐廳花費時間（秒）',
        type: 'scatter',
        marker: {
            color: '#5999d4',
            opacity: 0.8,
          }
      };
      
    let trace2 = {
        x: x,
        y: detailRunTime,
        name: '爬取可外送餐廳資訊花費時間（秒）',
        type: 'scatter',
        marker: {
            color: '#003585',
            opacity: 0.8,
          }
        };
    
    let data = [trace1, trace2];
    let plotTitle = ''
    if (source == 'ue'){plotTitle = 'Uber Eats 爬取時間'}
    else {plotTitle = 'Food Panda 爬取時間'}
    let layout = {
        title: {
            text: plotTitle,
            font: {
              size: 18
            },
            x: 0.15,
            y: 0.985
          },
        legend: {
            "orientation": "h",
            "y" : 1.16
        },
        margin: { 
            t: 70,
            b: 70
        }
    }
    let graph = document.getElementById(source.concat('-lambda-line-graph'))
    Plotly.newPlot(graph, data, layout);
}

function renderMDinerCountGraph(infoArray, source){
    let x = infoArray[0]
    let mMatchedDinerCount = infoArray[1]
    let mUnmatchedDinerCount = infoArray[2]
    let plotConf = [
        {
            histfunc: "sum",
            y: mUnmatchedDinerCount,
            x: x,
            type: "bar",
            name: "不同",
            marker: {
                color: '#5999d4',
                opacity: 0.8,
              }
        },
        {
            histfunc: "sum",
            y: mMatchedDinerCount,
            x: x,
            type: "bar",
            name: "相同",
            marker: {
                color: '#003585',
                opacity: 0.8,
            }
        }
    ]
    let plotTitle = 'Uber Eats, Food Panda 餐廳比對結果'
    let layout = {
        title: {
            text: plotTitle,
            font: {
              size: 18
            },
            x: 0.15,
            y: 0.985
          },
        legend: {
            "orientation": "h",
            "y" : 1.16
        },
        margin: { 
            t: 70,
            b: 70
        },
        barmode: 'stack'
    }
    let graph = document.getElementById(source.concat('-bar-graph'))
    Plotly.newPlot( graph, plotConf, layout );
}

function renderPDinerCountGraph(infoArray, source){
    let x = infoArray[0]
    let pAFC = infoArray[1]
    let pANFC = infoArray[2]
    let pUFC = infoArray[3]
    let pUNFC = infoArray[4]
    let plotConf = [
        {
            histfunc: "sum",
            y: pAFC,
            x: x,
            type: "bar",
            name: "有，以 Place API 查詢",
            marker: {
                color: '#003585',
                opacity: 0.8,
            }
        },
        {
            histfunc: "sum",
            y: pANFC,
            x: x,
            type: "bar",
            name: "沒有，以 Place API 查詢",
            marker: {
                color: '#5e33d4',
                opacity: 0.8,
            }
        },
        {
            histfunc: "sum",
            y: pUFC,
            x: x,
            type: "bar",
            name: "有，以現有資料更新",
            marker: {
                color: '#5999d4',
                opacity: 0.8,
            }
        },
        {
            histfunc: "sum",
            y: pUNFC,
            x: x,
            type: "bar",
            name: "沒有，以現有資料更新",
            marker: {
                color: '#2735f8',
                opacity: 0.8,
            }
        }
    ]
    let graph = document.getElementById(source.concat('-bar-graph'))
    let plotTitle = 'Google Map 資料查詢結果'
    let layout = {
        title: {
            text: plotTitle,
            font: {
              size: 18
            },
            x: 0.15,
            y: 0.985
          },
        legend: {
            "orientation": "h",
            "y" : 1.16
        },
        margin: { 
            t: 70,
            b: 70
        },
        barmode: 'stack'
    }
    Plotly.newPlot( graph, plotConf, layout);
}

function renderMRunTimeGraph(infoArray, source){
    let x = infoArray[0]
    let mRunTime = infoArray[1]
    let trace1 = {
        x: x,
        y: mRunTime,
        name: '花費時間（秒）',
        type: 'scatter'
      };
      
    let data = [trace1];
    let graph = document.getElementById(source.concat('-line-graph'))
    let plotTitle = 'Uber Eats, Food Panda 餐廳比對花費時間（秒）'
    let layout = {
        title: {
            text: plotTitle,
            font: {
              size: 18
            },
            x: 0.15,
            y: 0.985
          },
        legend: {
            showlegend: false
        },
        margin: { 
            t: 70,
            b: 70
        }
    }
    Plotly.newPlot(graph, data, layout);
}

function renderPRunTimeGraph(infoArray, source){
    let x = infoArray[0]
    let pRunTime = infoArray[1]
    let trace1 = {
        x: x,
        y: pRunTime,
        name: 'place',
        type: 'scatter'
      };
      
    let data = [trace1];
    let graph = document.getElementById(source.concat('-line-graph'))
    let plotTitle = 'Google Map 資料查詢花費時間（秒）'
    let layout = {
        title: {
            text: plotTitle,
            font: {
              size: 18
            },
            x: 0.15,
            y: 0.985
          },
        legend: {
            showlegend: false
        },
        margin: { 
            t: 70,
            b: 70
        }
    }
    Plotly.newPlot(graph, data, layout);
}

function endGTStartWarn(){
    Swal.fire(
        {
        icon: 'warning',
        title: '結束日期要早於開始日期',
        customClass: 'justify-content-center'
    })
}

initPost(dashboardApi, initData)

document.getElementById('select-dates').addEventListener('change', (e)=>{
    let startDate = startDateDom.value
    let endDate = endDateDom.value
    let startTime = startTimeDom.value
    let endTime = endTimeDom.value
    if (moment(endDate).isBefore(moment(startDate))){
        endGTStartWarn()
    } else {
    let data = {"start_date_time": `${startDate} ${startTime}`, "end_date_time": `${endDate} ${endTime}`}
    showLoading()
    ajaxPost(dashboardApi, data, function(response){
        resetTableS()
        resetGraphS()
        renderDashBoard(response)
        endLoading()
    })
    }
})

function setIntervalAndExecute(fn, startTimeout, stopTimeout){
    fn();
    setTimeout(function(){
        intervalId = setInterval(fn, 3000)
    }, startTimeout)
    setTimeout(function(){
        clearInterval(intervalId)
    }, stopTimeout
    )
}

if (utcNow.isBetween(todayStartRefresh, todayEndRefresh)){
    let startTimer = 0
    let endTimer = moment.duration(utcNow.diff(todayEndRefresh)).asMilliseconds()
    setTimeout(function(){
        setIntervalAndExecute(autoUpadte, startTimer, endTimer) 
    }, startTimer)

} else if (utcNow.isBefore(todayStartRefresh)){
    let startTimer = moment.duration(todayStartRefresh.diff(utcNow)).asMilliseconds()
    let endTimer = moment.duration(utcNow.diff(todayEndRefresh)).asMilliseconds()
    setTimeout(function(){
        setIntervalAndExecute(autoUpadte, startTimer, endTimer) 
    }, startTimer)
}