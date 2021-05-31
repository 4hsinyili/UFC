// API related variables
let filtersAPI = 'api/v1/filters'
let dinerSearchAPI = 'api/v1/dinersearch'
let dinerShuffleAPI = 'api/v1/dinershuffle'
let domain = window.location.origin
let dinerInfoRoute = domain.concat('/dinerinfo')
let initData = {'condition': {}, 'offset': 0}
let openDaysMap = {
    1: 'Mon.',
    2: 'Tue.',
    3: 'Wed.',
    4: 'Thu.',
    5: 'Fri.',
    6: 'Sat.',
    7: 'Sun.',
}

// Doms
let diners = document.getElementById('diners')
let filters = document.getElementById('filters')
let dinerTemplate = document.getElementById('diner-tamplate')
let dinersHtml = diners.innerHTML

let ratingSvg = document.querySelector('[name="rating_svg"]')
let viewCountSvg = document.querySelector('[name="view_count_svg"]')
let budgetSvg = document.querySelector('[name=budget_svg]')

let filter0 = $('div[name=filter][data-number=0]')[0]
let sorter0 = $('div[name=sorter][data-number=0]')[0]
let filtersSection = $('div[id="filters-section"]')[0]
let sortersSection = $('div[id="sorters-section"]')[0]

let addNewFilterDom = $('div[name="add-new-filter')[0]
let clearFilterDom = $('div[name="clear-filter"]')[0]
let clearAllFilterDom = $('div[name="clear-all-filter"]')[0]

let addNewSorterDom = $('div[name="add-new-sorter"]')[0]
let clearSorterDom = $('div[name="clear-sorter"]')[0]
let clearAllSorterDom = $('div[name="clear-all-sorter"]')[0]

let sendFilterDom = $('div[name="send-filters"]')[0]
let showMoreDom = $('div[id="show-more"]')[0]

let searchBox = $('#search-box')[0]
let searchButton = $('#search-button')[0]
let shuffleButton = $('#shuffle')[0]
let toggleFiltersDom = $('#toggle-filters')[0]
let toggleSortersDom = $('#toggle-sorters')[0]

// Define functions
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

function ajaxGet(src, callback){
    let initialUrl = src;
    let initaialXhr = new XMLHttpRequest();
    initaialXhr.open('GET', initialUrl, true);
    initaialXhr.onload = function() {
    if (initaialXhr.status >= 200 && initaialXhr.status < 400) {
        let data = JSON.parse(initaialXhr.responseText);
        callback(data)
    }
    };
    initaialXhr.send();
} 

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

function clearDIners(){
    diners.innerHTML = dinersHtml
}

function renderDinerInfo(dinerInfo, dinerNode, source){
    let title = dinerInfo['title_'.concat(source)]
    console.log(title)
    let image = dinerInfo['image_'.concat(source)]
    let rating = dinerInfo['rating_'.concat(source)]
    let viewCount = dinerInfo['view_count_'.concat(source)]
    let budget = dinerInfo['budget_'.concat(source)]
    let link = dinerInfo['link_'.concat(source)]
    let redirectUrl = dinerInfo['redirect_url']
    let titleNode = dinerNode.querySelector('.title_'.concat(source))
    titleNode.innerText = title
    let imageNode = dinerNode.querySelector('.image_'.concat(source))
    imageNode.setAttribute('src', image)
    let ratingNode = dinerNode.querySelector('.rating_'.concat(source))
    ratingNode.querySelector('.rating_value_'.concat(source)).innerText = rating
    let newRatingSvg = ratingSvg.cloneNode(true)
    $(newRatingSvg).show()
    $(ratingNode).prepend(newRatingSvg)
    let viewCountNode = dinerNode.querySelector('.view_count_'.concat(source))
    viewCountNode.querySelector('.view_count_value_'.concat(source)).innerText = viewCount
    let newViewCountSvg = viewCountSvg.cloneNode(true)
    $(newViewCountSvg).show()
    $(viewCountNode).prepend(newViewCountSvg)
    let budgetNode = dinerNode.querySelector('.budget_'.concat(source))
    budgetNode.querySelector('.budget_value_'.concat(source)).innerText = '$'.repeat(budget)
    let newBudgetSvg = budgetSvg.cloneNode(true)
    $(newBudgetSvg).show()
    $(budgetNode).prepend(newBudgetSvg)
    let infoNode = dinerNode.querySelector('.info_'.concat(source))
    infoNode.setAttribute('href', link)
    let redirectHrefNode = dinerNode.querySelectorAll('.redirect-href_'.concat(source))
    for (let i = 0; i < redirectHrefNode.length; i++){
        redirectHrefNode[i].setAttribute('href', redirectUrl)
    }
    return dinerNode
}

function renderDiner(diner){
    let dinerNode = dinerTemplate.cloneNode(true)
    let diner_uuid_ue = diner['uuid_ue']
    let diner_uuid_fp = diner['uuid_fp']
    let redirectUrl = dinerInfoRoute.concat('?uuid_ue=').concat(diner_uuid_ue).concat('&uuid_fp=').concat(diner_uuid_fp)
    let diner_info_ue = false
    let diner_info_fp = false
    if (diner_uuid_ue != ''){
        diner_info_ue = {
            "title_ue": diner['title_ue'],
            "rating_ue": diner['rating_ue'],
            "view_count_ue": diner['view_count_ue'],
            "budget_ue": diner['budget_ue'],
            "image_ue": diner["image_ue"],
            "link_ue": diner["link_ue"],
            "redirect_url": redirectUrl
        }
    }
    if (diner_uuid_fp != ''){
        diner_info_fp = {
            "title_fp": diner['title_ue'],
            "rating_fp": diner['rating_fp'],
            "view_count_fp": diner['view_count_fp'],
            "budget_fp": diner['budget_fp'],
            "image_fp": diner["image_fp"],
            "link_fp": diner["link_fp"],
            "redirect_url": redirectUrl
        }
    }
    if (diner_info_ue){ renderDinerInfo(diner_info_ue, dinerNode, 'ue')}
    if (diner_info_fp){ renderDinerInfo(diner_info_fp, dinerNode, 'fp')}
    return dinerNode
}

function renderList(data){
    let results = data.data
    console.log(results)
    for (let i = 0; i < results.length; i++){
        let diner = results[i]
        diner = renderDiner(diner)
        diners.appendChild(diner)
        $(diner).show()
    }
    console.log(data)
    if (data.has_more == true){
        showMoreDom.setAttribute('data-offset', data.next_offset)
        $(showMoreDom).show()
    } else {
        $(showMoreDom).hide()
    }
    }

function renderMore(data){
    renderList(data)
    window.scrollTo(0,document.body.scrollHeight);
}

function createConditions(keyWord){
    let conditions = {}
    if (keyWord){conditions['keyword'] = keyWord}
    return conditions
}

function appendFilter(){
    let filterSet = $('div[name="filter"]')
    let newFilter = filter0.cloneNode(true)
    let newFilterNumber = filterSet.length
    newFilter.setAttribute('data-number', newFilterNumber)
    let newFilterWithDatanumbers = $(newFilter).find("[data-number]")
    newFilter.setAttribute('data-number', newFilterNumber)
    for (let i = 0; i < newFilterWithDatanumbers.length; i++){
        newFilterWithDatanumbers[i].setAttribute('data-number', newFilterNumber)
    }
    filters.appendChild(newFilter)
    let removeButton = document.querySelector(`[name="clear-filter"][data-number="${newFilterNumber}"]`)
    removeButton.classList.add('remove-filter')
    removeButton.innerHTML = `<img class="button" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/remove_filter.svg" data-number=${newFilterNumber}>`
    renderFilters()
    removeButton.addEventListener('click', (e)=>{
        removeFilter(e.target)
    })
}

function removeFilter(target){
    let dataNumber = parseInt(target.getAttribute('data-number'))
    let needRemove = document.querySelector(`[name="filter"][data-number="${dataNumber}"]`)
    needRemove.remove()
    let filters = document.querySelectorAll('[name="filter"]')
    for (let i = 0; i < filters.length; i++){
        filters[i].setAttribute('data-number', i)
        let dataNumbers = $(filters[i]).find('[data-number]')
        for (let r = 0; r < dataNumbers.length; r++){
            dataNumbers[r].setAttribute('data-number', i)
        }
    }
}

function clearFilter(target){
    let dataNumber = parseInt(target.getAttribute('data-number'))
    let selects = $(filters).find(`select[data-number=${dataNumber}]`)
    for (let i = 0; i < selects.length; i++){
        selects[i].value = 'default'
        if (selects[i].getAttribute('name') != 'filter-source'){
            $(selects[i]).prop('disabled', 'disabled')
        }
    }
}

function clearAllFilter(){
    $(filtersSection).hide()
    clearFilter(clearFilterDom)
    let removeFilters = $('[class*="remove-filter"]')
    for( let i = 0; i < removeFilters.length; i ++){
        removeFilter(removeFilters[i])
    }
}

function renderOptions(data, source){
    let deliver_fee = data.data['deliver_fee_'.concat(source)]
    let deliver_time = data.data['deliver_time_'.concat(source)]
    let budget = data.data['budget_'.concat(source)]
    let rating = data.data['rating_'.concat(source)]
    let view_count = data.data['view_count_'.concat(source)]
    let tags = data.data['tags_'.concat(source)]
    let filterValue0 =  $('div[name="filter-value"][data-number="0"]')[0]
    let deliver_fee_select = $(filterValue0).find(".deliver_fee_".concat(source))[0]
    let deliver_time_select = $(filterValue0).find(".deliver_time_".concat(source))[0]
    let budget_select = $(filterValue0).find(".budget_".concat(source))[0]
    let rating_select = $(filterValue0).find(".rating_".concat(source))[0]
    let view_count_select = $(filterValue0).find(".view_count_".concat(source))[0]
    let tags_select = $(filterValue0).find(".tags_".concat(source))[0]
    let datas = [deliver_fee, deliver_time, budget, rating, view_count, tags]
    let selects = [deliver_fee_select, deliver_time_select, budget_select, rating_select, view_count_select, tags_select]
    for (let i = 0; i < datas.length; i++){
        for (let r = 0; r < datas[i].length; r++){
            let option_value = datas[i][r]
            let option = document.createElement('option')
            option.value =  option_value
            option.setAttribute('data-type', typeof option_value)
            option.innerText = option_value
            selects[i].appendChild(option)
        }
    }
}

function renderFilter(dataNumber){
    let eachFilterSource = $(`select[name="filter-source"][data-number=${dataNumber}]`)
    let eachFilterType =  $(`select[name="filter-type"][data-number=${dataNumber}]`)
    let eachFilterOperator = $(`select[name="filter-operator"][data-number=${dataNumber}]`)
    let eachFilterValue =  $(`select[name="filter-value"][data-number=${dataNumber}]`)
    for(let r=0; r<eachFilterType.length; r++){
        $(eachFilterType[r]).hide();
    }
    $(eachFilterType[0]).show().prop('disabled', 'disabled')
    for(let r=0; r<eachFilterOperator.length; r++){
        $(eachFilterOperator[r]).hide();
    }
    $(eachFilterOperator[0]).show().prop('disabled', 'disabled')
    for(let r=0; r<eachFilterValue.length; r++){
        $(eachFilterValue[r]).hide();
    }
    $(eachFilterValue[0]).show().prop('disabled', 'disabled')

    let chosedFilterType = $(`select[name*="filter-type"][data-number=${dataNumber}][class*="${eachFilterSource.val()}"]`)
    if (chosedFilterType.length == 1){
        $(eachFilterType[0]).hide()
        $(chosedFilterType).show().prop('disabled', false)
    };
    let chosedFilterOperator = $(`select[name="filter-operator"][data-number=${dataNumber}].${chosedFilterType.val()}.${eachFilterSource.val()}`)
    if (chosedFilterOperator.length == 1){
        $(eachFilterOperator[0]).hide()
        $(chosedFilterOperator).show().prop('disabled', false)
    };
    let chosedFilterValue = $(`select[name="filter-value"][data-number=${dataNumber}].${chosedFilterType.val()}.${eachFilterSource.val()}`);
    if (chosedFilterValue.length == 1){
        $(eachFilterValue[0]).hide()
        $(chosedFilterValue).show().prop('disabled', false)
    };
}

function renderFilters(){
    let filterSet = $('div[name="filter"]')
    let filterSetLength = filterSet.length
    for (let i = 0; i < filterSetLength; i++){
        renderFilter(i)
    };
}

function turnFIltersToConditions(conditions, filterSet){
    conditions['filter'] = []
    for (let i = 0; i < filterSet.length; i ++){
        tFSelects = $(filterSet[i]).find('select')
        conditions['filter'].push({})
        let last = conditions['filter'].length - 1
        for (let r = 0; r < tFSelects.length; r ++){
            if ($(tFSelects[r]).css('display') != 'none'){
                if (tFSelects[r].getAttribute('name') == 'filter-type'){
                    conditions['filter'][last]['field'] = $(tFSelects[r]).val()
                } else if (tFSelects[r].getAttribute('name') == 'filter-operator'){
                    conditions['filter'][last]['filter'] = $(tFSelects[r]).val()
                }else if  (tFSelects[r].getAttribute('name') == 'filter-value'){
                    if (tFSelects[r].getAttribute('data-type') == 'number'){
                        conditions['filter'][last]['value'] = parseInt($(tFSelects[r]).val())
                    } else if (tFSelects[r].getAttribute('data-type') == 'string'){
                        conditions['filter'][last]['value'] = $(tFSelects[r]).val()
                    } else if (tFSelects[r].getAttribute('data-type') == 'float'){
                        conditions['filter'][last]['value'] = parseFloat($(tFSelects[r]).val())
                    }
                }
            }
        }
    }
    return conditions
}

function appendSorter(){
    let sorterSet = $('div[name="sorter"]')
    let newSorter = sorter0.cloneNode(true)
    let newSorterNumber = sorterSet.length
    newSorter.setAttribute('data-number', newSorterNumber)
    let newSorterWithDatanumbers = $(newSorter).find("[data-number]")
    newSorter.setAttribute('data-number', newSorterNumber)
    for (let i = 0; i < newSorterWithDatanumbers.length; i++){
        newSorterWithDatanumbers[i].setAttribute('data-number', newSorterNumber)
    }
    sorters.appendChild(newSorter)
    let removeButton = document.querySelector(`[name="clear-sorter"][data-number="${newSorterNumber}"]`)
    removeButton.classList.add('remove-sorter')
    removeButton.innerHTML = `<img class="button" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/remove_sorter.svg" data-number=${newSorterNumber}>`
    renderSorters()
    removeButton.addEventListener('click', (e)=>{
        removeSorter(e.target)
    })
}

function removeSorter(target){
    let dataNumber = parseInt(target.getAttribute('data-number'))
    let needRemove = document.querySelector(`[name="sorter"][data-number="${dataNumber}"]`)
    needRemove.remove()
    let sorters = document.querySelectorAll('[name="sorter"]')
    for (let i = 0; i < sorters.length; i++){
        sorters[i].setAttribute('data-number', i)
        let dataNumbers = $(sorters[i]).find('[data-number]')
        for (let r = 0; r < dataNumbers.length; r++){
            dataNumbers[r].setAttribute('data-number', i)
        }
    }
}

function clearSorter(target){
    let dataNumber = parseInt(target.getAttribute('data-number'))
    console.log(dataNumber)
    let selects = $(sorters).find(`select[data-number=${dataNumber}]`)
    for (let i = 0; i < selects.length; i++){
        selects[i].value = 'default'
        if (selects[i].getAttribute('name') != 'sorter-source'){
            $(selects[i]).prop('disabled', 'disabled')
        }
    }
}


function clearAllSorter(){
    $(sortersSection).hide()
    clearSorter(clearSorterDom)
    let removeSorters = $('[class*="remove-sorter"]')
    for( let i = 0; i < removeSorters.length; i ++){
        removeSorter(removeSorters[i])
    }
}

function renderSorter(dataNumber){
    let eachSorterSource = $(`select[name="sorter-source"][data-number=${dataNumber}]`)
    let eachSorterType =  $(`select[name="sorter-type"][data-number=${dataNumber}]`)
    let eachSorterOperator = $(`select[name="sorter-operator"][data-number=${dataNumber}]`)
    for(let r=0; r<eachSorterType.length; r++){
        $(eachSorterType[r]).hide();
    }
    $(eachSorterType[0]).show().prop('disabled', 'disabled')
    for(let r=0; r<eachSorterOperator.length; r++){
        $(eachSorterOperator[r]).hide();
    }
    $(eachSorterOperator[0]).show().prop('disabled', 'disabled')

    let chosedSorterType = $(`select[name*="sorter-type"][data-number=${dataNumber}][class*="${eachSorterSource.val()}"]`)
    if (chosedSorterType.length == 1){
        $(eachSorterType[0]).hide()
        $(chosedSorterType).show().prop('disabled', false)
    };

    let chosedSorterOperator = $(`select[name="sorter-operator"][data-number=${dataNumber}].${chosedSorterType.val()}.${eachSorterSource.val()}`)
    if (chosedSorterOperator.length == 1){
        $(eachSorterOperator[0]).hide()
        $(chosedSorterOperator).show().prop('disabled', false)
    };
}

function renderSorters(){
    let sorterSet = $('div[name="sorter"]')
    let sorterSetLength = sorterSet.length
    for (let i = 0; i < sorterSetLength; i++){
        renderSorter(i)
    };
}

function turnSortersToConditions(conditions, sorterSet){
    conditions['sorter'] = []
    for (let i = 0; i < sorterSet.length; i ++){
        tFSelects = $(sorterSet[i]).find('select')
        conditions['sorter'].push({})
        let last = conditions['sorter'].length - 1
        for (let r = 0; r < tFSelects.length; r ++){
            if ($(tFSelects[r]).css('display') != 'none'){
                if (tFSelects[r].getAttribute('name') == 'sorter-type'){
                    conditions['sorter'][last]['field'] = $(tFSelects[r]).val()
                } else if (tFSelects[r].getAttribute('name') == 'sorter-operator'){
                    conditions['sorter'][last]['sorter'] = parseInt($(tFSelects[r]).val())
                }
            }
        }
    }
    return conditions
}

function search(offset){
    $(showMoreDom).hide()
    let keyWord = document.getElementById('search-box')
    let filterSet = $('div[name="filter"]')
    let sorterSet = $('div[name="sorter"]')
    conditions = createConditions($(keyWord).val())
    conditions = turnFIltersToConditions(conditions, filterSet)
    conditions = turnSortersToConditions(conditions, sorterSet)
    console.log(conditions)
    data = {'condition': conditions, 'offset': offset}
    ajaxPost(dinerSearchAPI, data, function(response){
        renderList(response)
    })
}

function shuffle(){
    ajaxPost(dinerShuffleAPI, null, function(response){
        renderList(response)
    })
}

// start to render
ajaxPost(dinerSearchAPI, initData, function(response){
    renderList(response)
})

ajaxGet(filtersAPI, function(response){
    renderFilters();
    renderOptions(response, 'ue');
    renderOptions(response, 'fp');
})

renderSorters()

filters.addEventListener('change', (e)=>{
    if ($(e.target).attr('name') == 'filter-source' || $(e.target).attr('name') == 'filter-type'){
        let dataNumber = e.target.getAttribute('data-number')
        renderFilter(dataNumber)
    }
})

sorters.addEventListener('change', (e)=>{
    if ($(e.target).attr('name') == 'sorter-source' || $(e.target).attr('name') == 'sorter-type'){
        let dataNumber = e.target.getAttribute('data-number')
        renderSorter(dataNumber)
    }
})

$(toggleFiltersDom).click(function(){
    $(sortersSection).hide()
    $(filtersSection).toggle()
})

$(toggleSortersDom).click(function(){
    $(filtersSection).hide()
    $(sortersSection).toggle()
})

addNewFilterDom.addEventListener('click', (e)=>{
    appendFilter()
})

clearFilterDom.addEventListener('click', (e)=>{
    clearFilter(e.target)
})

clearAllFilterDom.addEventListener('click', (e)=>{
    clearAllFilter()
    clearDIners()
    search(0)
})

addNewSorterDom.addEventListener('click', (e)=>{
    appendSorter()
})

clearSorterDom.addEventListener('click', (e)=>{
    clearSorter(e.target)
})

clearAllSorterDom.addEventListener('click', (e)=>{
    clearAllSorter()
    clearDIners()
    search(0)
})

$(sendFilterDom).click(function(){
    clearDIners()
    $(filtersSection).hide()
    $(sortersSection).hide()
    search(0)
})

$(searchButton).click(function(){
    clearDIners()
    $(filtersSection).hide()
    $(sortersSection).hide()
    search(0)
})

$(searchBox).keydown(function(e){
    if (e.keyCode == 13){
        $(filtersSection).hide()
        $(sortersSection).hide()
        clearDIners()
        search(0)
    }
})

$(shuffleButton).click(function(){
    clearDIners()
    $(showMoreDom).hide()
    shuffle()
})

$(showMoreDom).click(function(){
    let offset = parseInt(showMoreDom.getAttribute('data-offset'))
    search(offset)
})