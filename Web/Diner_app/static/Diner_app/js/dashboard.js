let today = new Date();
let dd = String(today.getDate()).padStart(2, '0');
let mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
let yyyy = today.getFullYear();
let startDateDom = document.querySelector('#start-date')
let endDateDom = document.querySelector('#end-date')
let dateFormvalue = `${yyyy}-${mm}-${dd}`
startDateDom.value = dateFormvalue
endDateDom.value = dateFormvalue
let initData = {"start_date": dateFormvalue, "end_date": dateFormvalue}

let lambdaDinerCountGraph = document.getElementById('lambda-hist-graph');
let lambdaRuntimeGraph = document.getElementById('lambda-line-graph');
let mDinerCountGraph = document.getElementById('m-hist-graph');
let pDinerCountGraph = document.getElementById('p-hist-graph');
let mpRunTimeGraph = document.getElementById('mp-line-graph');
let dashboardApi = 'api/v1/dashboard';

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

function ajaxPost(src, params, callback){
    let initialUrl = src;
    let initaialXhr = new XMLHttpRequest();
    initaialXhr.open('POST', initialUrl, true);
    initaialXhr.setRequestHeader('Content-type', 'application/json')
    initaialXhr.setRequestHeader('X-CSRFToken', csrftoken)
    initaialXhr.setRequestHeader('Accept', '*/*')
    initaialXhr.send(JSON.stringify(params))
    initaialXhr.onload = function() {
    if (initaialXhr.status >= 200 && initaialXhr.status < 400) {
        let data = JSON.parse(initaialXhr.responseText);
        callback(data)
    }
    };
} 

function initPost(dashboardApi, data){
    ajaxPost(dashboardApi, data, function(response){
        console.log(response)
        renderDashBoard(response)
    })
}

function renderDashBoard(response){
    let data = response.data.trigger_log_data
    let ueListStartData = data.get_ue_list_start
    let ueListData = data.get_ue_list
    ueListInfo = renderList(ueListStartData, ueListData, 'ue-list')
    
    let ueDetailData = data.get_ue_detail
    ueDetailInfo = renderDetail(ueListInfo, ueDetailData, 'ue-detail')
    
    let fpListStartData = data.get_fp_list_start
    let fpListData = data.get_fp_list
    fpListInfo = renderList(fpListStartData, fpListData, 'fp-list')
    
    let fpDetailData = data.get_fp_detail
    fpDetailInfo = renderDetail(fpListInfo, fpDetailData, 'fp-detail')
    
    // let matchStartData = data.match_start
    // let matchData = data.match
    // matchInfo = renderMatch(matchStartData, matchData, 'match')
    
    // let placeStartData = data.place_start
    // let placeData = data.place
    // placeInfo = renderPlace(placeStartData, placeData, 'place')
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
    row.querySelector(`[data-cell="api-count"]`).innerText = info.api_count
    row.querySelector(`[data-cell="diner-count"]`).innerText = info.diner_count
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
        console.log('old data')
        return false
    }
    let branchesCount = listStartData.length
    let runTimeArray = new Array()
    let dinerCountArray = new Array()
    let startTimeArray = new Array()
    let endTimeArray = new Array()
    for (let i=0; i<listStartData.length; i++){
        let startData = listStartData[i]
        let runData = listData[i]
        let startTime = moment(startData.log_time).add(8, 'hours');
        let endTime = moment(runData.log_time).add(8, 'hours');
        let runTime = moment.duration(endTime.diff(startTime)).asMilliseconds() / 1000
        let dinerCount = runData.records_count
        runTimeArray.push(runTime)
        dinerCountArray.push(dinerCount)
        startTimeArray.push(startTime)
        endTimeArray.push(endTime)
        }
    let runTimeAvg = sumData(runTimeArray) / runTimeArray.length
    let dinerCountTotal = sumData(dinerCountArray)
    let startTimeMin = moment.min(startTimeArray).format('YYYY-MM-DD HH:mm:ss')
    let endTimeMax = moment.max(endTimeArray).format('YYYY-MM-DD HH:mm:ss')
    let info = {
        'branches_count': branchesCount,
        'run_time': runTimeAvg,
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
    let startData = matchStartData[0]
    let runData = matchData[0]
    let startTime = moment(startData.log_time).add(8, 'hours');
    let endTime = moment(runData.log_time).add(8, 'hours');
    let runTime = moment.duration(endTime.diff(startTime)).asMilliseconds() / 1000
    let dinerCount = runData.records_count
    let matchCount = runData.matched_count
    let info = {
        'run_time': runTime,
        'diner_count': dinerCount,
        'match_count': matchCount,
        'start_time': startTime.format('YYYY-MM-DD HH:mm:ss'),
        'end_time': endTime.format('YYYY-MM-DD HH:mm:ss')
    }
    appendRow('match-table', rowType, info)
    return info
}

function renderPlace(placeStartData, placeData, rowType){
    if ((!placeStartData) || (!placeData)){
        return false
    }
    let startData = placeStartData[0]
    let runData = placeData[0]
    let startTime = moment(startData.log_time).add(8, 'hours');
    let endTime = moment(runData.log_time).add(8, 'hours');
    let runTime = moment.duration(endTime.diff(startTime)).asMilliseconds() / 1000
    let apiCount = runData.records_count
    let updateFoundCount = runData.update_found_count
    let updateNotFoundCount = runData.update_not_found_count
    let dinerCount = apiCount + updateFoundCount + updateNotFoundCount
    let info = {
        'run_time': runTime,
        'api_count': apiCount,
        'diner_count': dinerCount,
        'update_found_count': updateFoundCount,
        'update_not_found_count': updateNotFoundCount,
        'start_time': startTime.format('YYYY-MM-DD HH:mm:ss'),
        'end_time': endTime.format('YYYY-MM-DD HH:mm:ss')
    }
    appendRow('place-table', rowType, info)
    return info
}

function resetTable(){
    let rows = document.querySelectorAll('[data-number]:not([data-number="0"])')
    for (let i=0; i < rows.length; i++){
        rows[i].remove()
    }
}

function renderLambdaDinerCountGraph(ueListInfo, ueDinerInfo, fpListInfo, fpDinerInfo){
    let x = ["2021-06-10 20:40:00", "2021-06-11 20:40:00"]
    let ueListDinerCount = [3600, 3500]
    let ueDetailDinerCount = [1300, 1350]
    let fpListDinerCount = [2700, 2702]
    let fpDetailDinerCount = [2600, 2590]
    let plotConf = [
        {
            histfunc: "sum",
            y: ueListDinerCount,
            x: x,
            type: "histogram",
            name: "get_ue_list"
          },
          {
            histfunc: "sum",
            y: ueDetailDinerCount,
            x: x,
            type: "histogram",
            name: "get_ue_detail"
          },
          {
            histfunc: "sum",
            y: fpListDinerCount,
            x: x,
            type: "histogram",
            name: "get_fp_list"
          },
          {
            histfunc: "sum",
            y: fpDetailDinerCount,
            x: x,
            type: "histogram",
            name: "get_fp_detail"
          }
    ]
    Plotly.newPlot( lambdaDinerCountGraph, plotConf, {
    margin: { t: 0 } } );
}

function renderLambdaRunTimeGraph(){
    let trace1 = {
        x: ["2021-06-10 20:40:00", "2021-06-11 20:40:00", "2021-06-12 20:40:00", "2021-06-13 20:40:00"],
        y: [200, 310, 233, 323],
        name: 'get_ue_list',
        type: 'scatter'
      };
      
    let trace2 = {
        x: ["2021-06-10 20:40:00", "2021-06-11 20:40:00", "2021-06-12 20:40:00", "2021-06-13 20:40:00"],
        y: [2, 3, 2, 3],
        name: 'get_fp_list',
        type: 'scatter'
        };
    
    let data = [trace1, trace2];
    
    Plotly.newPlot(lambdaRuntimeGraph, data, {margin: { t: 0 }});
}

function renderMDinerCountGraph(){
    let x = ["2021-06-10 20:40:00", "2021-06-11 20:40:00"]
    let mMatchedDinerCount = [500, 600]
    let mTotalDinerCount = [3100, 2900]
    let plotConf = [
        {
            histfunc: "sum",
            y: mMatchedDinerCount,
            x: x,
            type: "bar",
            name: "matched"
          },
          {
            histfunc: "sum",
            y: mTotalDinerCount,
            x: x,
            type: "bar",
            name: "unmatched"
          }
    ]
    Plotly.newPlot( mDinerCountGraph, plotConf, {
    margin: { t: 0 }, barmode: 'stack' } );
}

function renderPDinerCountGraph(){
    let x = ["2021-06-10 20:40:00", "2021-06-11 20:40:00"]
    let pAPICount = [300, 200]
    let pUFCount = [2700, 2902]
    let pUNFCount = [200, 198]
    let plotConf = [
        {
            histfunc: "sum",
            y: pAPICount,
            x: x,
            type: "bar",
            name: "matched"
        },
        {
            histfunc: "sum",
            y: pUFCount,
            x: x,
            type: "bar",
            name: "unmatched"
        },
        {
            histfunc: "sum",
            y: pUNFCount,
            x: x,
            type: "bar",
            name: "unmatched"
        }
    ]
    Plotly.newPlot( pDinerCountGraph, plotConf, {
    margin: { t: 0 }, barmode: 'stack' } );
}

function renderMPRunTimeGraph(){
    let trace1 = {
        x: ["2021-06-10 20:40:00", "2021-06-11 20:40:00", "2021-06-12 20:40:00", "2021-06-13 20:40:00"],
        y: [900, 810, 833, 873],
        name: 'match',
        type: 'scatter'
      };
      
    let trace2 = {
        x: ["2021-06-10 20:40:00", "2021-06-11 20:40:00", "2021-06-12 20:40:00", "2021-06-13 20:40:00"],
        y: [900, 200, 52, 43],
        name: 'place',
        type: 'scatter'
        };
    
    let data = [trace1, trace2];
    
    Plotly.newPlot(mpRunTimeGraph, data, {margin: { t: 0 }});
}

initPost(dashboardApi, initData)
renderLambdaDinerCountGraph()
renderLambdaRunTimeGraph()
renderMDinerCountGraph()
renderPDinerCountGraph()
renderMPRunTimeGraph()

document.getElementById('select-dates').addEventListener('change', (e)=>{
    let startDate = startDateDom.value
    let endDate = endDateDom.value
    let data = {'start_date': startDate, 'end_date': endDate}
    ajaxPost(dashboardApi, data, function(response){
        console.log(response)
        resetTable()
        renderDashBoard(response)
    })
})

// ajax(getUrl, function(response){
//     render(response); });

// setInterval(function(){ajax(`api/1.0/dashboard?scope=${scopeForm.value}&date=${dateForm.value}`, function(response){
//     render(response)
// })}, 5000);