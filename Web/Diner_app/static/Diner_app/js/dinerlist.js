// API related variables
let filtersAPI = 'api/v1/filters'
let dinerSearchAPI = 'api/v1/dinersearch'
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
let filter0 = $('div[data-number=0][class="row"]')[0]
let filtersSection = $('div[id="filters-section"]')[0]
let addNewFilterDom = $('div[name="add-new-filter')[0]
let clearFilterDom = $('div[name="clear-filter"]')[0]
let clearAllFilterDom = $('div[name="clear-all-filter"]')[0]
let sendFilterDom = $('div[name="send-filters"]')[0]
let showMoreDom = $('div[id="show-more"]')[0]
let toggleFiltersDom = $('div[id="toggle-filters"]')[0]


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

function renderList(data){
    let results = data.data
    for (let i = 0; i < results.length; i++){
        let result = results[i]
        let diner = dinerTemplate.cloneNode(true)
        let redirectUrl = dinerInfoRoute.concat('?diner_id=').concat(result.uuid)
        diner.classList.add('diner')
        let title = diner.querySelector('.title')
        title.innerText = result.title
        let image = diner.querySelector('.image')
        image.setAttribute('src', result.image)
        let rating = diner.querySelector('.rating')
        rating.innerText = 'ue rating: '.concat(result.rating)
        let viewCount = diner.querySelector('.view_count')
        viewCount.innerText = 'ue view_count: '.concat(result.view_count)
        let budget = diner.querySelector('.budget')
        budget.innerText = 'ue budget: '.concat('$'.repeat(result.budget))
        let ueInfo = diner.querySelector('.ue_info')
        ueInfo.setAttribute('href', result.link)
        let redirectHref = diner.querySelectorAll('.redirect-href')
        for (let i = 0; i < redirectHref.length; i++){
            redirectHref[i].setAttribute('href', redirectUrl)
        }
        diners.appendChild(diner)
        $(diner).show()
    }
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
    removeButton.innerText = 'remove-filter'
    renderFilters()
    removeButton.addEventListener('click', (e)=>{
        removeFilter(e.target)
    })
}

function removeFilter(target){
    target.parentNode.parentNode.removeChild(target.parentNode)
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
    let selects = $(target.parentNode).find('select')
    for (let i = 0; i < selects.length; i++){
        selects[i].value = 'default'
        if (selects[i].getAttribute('name') =='filter-operator'){
            $(selects[i]).hide()
        }
        if (selects[i].getAttribute('name') =='filter-value'){
            $(selects[i]).hide()
        }
    }
}

function clearAllFilter(){
    clearFilter(clearFilterDom)
    let removeFilters = $('[class*="remove-filter"]')
    for( let i = 0; i < removeFilters.length; i ++){
        removeFilter(removeFilters[i])
    }
}

function renderOptions(data){
    let deliver_fee = data.data.deliver_fee
    let deliver_time = data.data.deliver_time
    let budget = data.data.budget
    let rating = data.data.rating
    let view_count = data.data.view_count
    let tags = data.data.tags
    let filterValue0 =  $('div[name="filter-value"][data-number="0"]')[0]
    let deliver_fee_select = $(filterValue0).find("[class*=deliver_fee]")[0]
    let deliver_time_select = $(filterValue0).find("[class*=deliver_time]")[0]
    let budget_select = $(filterValue0).find("[class*=budget]")[0]
    let rating_select = $(filterValue0).find("[class*=rating]")[0]
    let view_count_select = $(filterValue0).find("[class*=view_count]")[0]
    let tags_select = $(filterValue0).find("[class*=tags]")[0]
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


function renderFilters(){
    let filterSet = $('div[name="filter"]')
    let filterSetLength = filterSet.length
    for (let i = 0; i < filterSetLength; i++){
        let eachFilterValue =  $(`select[name="filter-value"][data-number=${i}]`)
        let eachFilterOperator = $(`select[name="filter-operator"][data-number=${i}]`)
        let eachFilterType =  $(`select[name="filter-type"][data-number=${i}]`)
        for(let r=0; r<eachFilterValue.length; r++){
            $(eachFilterValue[r]).hide();
        }
        for(let r=0; r<eachFilterOperator.length; r++){
            $(eachFilterOperator[r]).hide();
        }
        $(`select[name="filter-operator"][data-number=${i}][class*="${eachFilterType.val()}"]`).show();
        $(`select[name="filter-value"][data-number=${i}][class*="${eachFilterType.val()}"]`).show();
    };
}

function turnFIltersToConditions(filterSet){
    let result = {}
    result['filter'] = []
    for (let i = 0; i < filterSet.length; i ++){
        tFSelects = $(filterSet[i]).find('select')
        result['filter'].push({})
        let last = result['filter'].length - 1
        for (let r = 0; r < tFSelects.length; r ++){
            if ($(tFSelects[r]).css('display') != 'none'){
                if (tFSelects[r].getAttribute('name') == 'filter-type'){
                    result['filter'][last]['field'] = $(tFSelects[r]).val()
                } else if (tFSelects[r].getAttribute('name') == 'filter-operator'){
                    result['filter'][last]['filter'] = $(tFSelects[r]).val()
                }else if  (tFSelects[r].getAttribute('name') == 'filter-value'){
                    if (tFSelects[r].getAttribute('data-type') == 'number'){
                        result['filter'][last]['value'] = parseInt($(tFSelects[r]).val())
                    } else if (tFSelects[r].getAttribute('data-type') == 'string'){
                        result['filter'][last]['value'] = $(tFSelects[r]).val()
                    } else if (tFSelects[r].getAttribute('data-type') == 'float'){
                        result['filter'][last]['value'] = parseFloat($(tFSelects[r]).val())
                    }
                }
            }
        }
    }
    return result
}


// start to render
ajaxPost(dinerSearchAPI, initData, function(response){
    renderList(response)
})

ajaxGet(filtersAPI, function(response){
    renderFilters();
    renderOptions(response);
})

filters.addEventListener('change', (e)=>{
    if ($(e.target).attr('name') == 'filter-type'){
        let option = $(e.target).val()
        let dataNumber = $(e.target).attr('data-number')
        let eachFilterOperator = $(`select[name="filter-operator"][data-number=${dataNumber}]`)
        let eachFilterValue =  $(`select[name="filter-value"][data-number=${dataNumber}]`)
        for(let r=0; r<eachFilterOperator.length; r++){$(eachFilterOperator[r]).hide();};
        for(let r=0; r<eachFilterValue.length; r++){$(eachFilterValue[r]).hide();};
        $(`select[name="filter-operator"][data-number=${dataNumber}][class*=${option}]`).show();
        $(`select[name="filter-value"][data-number=${dataNumber}][class*=${option}]`).show();
    }
})

$(toggleFiltersDom).click(function(){
    $(filtersSection).toggle()
})

addNewFilterDom.addEventListener('click', (e)=>{
    appendFilter()
})

clearFilterDom.addEventListener('click', (e)=>{
    clearFilter(e.target)
})

clearAllFilterDom.addEventListener('click', (e)=>{
    clearAllFilter()
    let filterSet = $('div[name="filter"]')
    result = turnFIltersToConditions(filterSet)
    console.log(result)
    data = {'condition': result, 'offset': 0}
    ajaxPost(dinerSearchAPI, data, function(response){
        clearDIners()
        renderList(data)
    })
})

$(sendFilterDom).click(function(){
    let filterSet = $('div[name="filter"]')
    result = turnFIltersToConditions(filterSet)
    console.log(result)
    data = {'condition': result, 'offset': 0}
    ajaxPost(dinerSearchAPI, data, function(response){
        clearDIners()
        renderList(response)
    })
})

$(showMoreDom).click(function(){
    let offset = parseInt(showMoreDom.getAttribute('data-offset'))
    let filterSet = $('div[name="filter"]')
    result = turnFIltersToConditions(filterSet)
    data = {'condition': result, 'offset': offset}
    ajaxPost(dinerSearchAPI, data, function(response){
        renderMore(response)
    })
})