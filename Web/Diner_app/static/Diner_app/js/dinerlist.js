// API related variables
let filtersAPI = 'api/v1/filters'
let dinerSearchAPI = 'api/v1/dinersearch'
let dinerShuffleAPI = 'api/v1/dinershuffle'
let favoritesAPI = 'api/v1/favorites'
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
let dinerTemplate = document.getElementById('diner-template')
let dinersHtml = diners.innerHTML

let ratingSvg = document.querySelector('[name="rating_svg"]')
let viewCountSvg = document.querySelector('[name="view_count_svg"]')
let budgetSvg = document.querySelector('[name=budget_svg]')

let filter0 = $('div[name=filter][data-number=0]')[0]
let sorter0 = $('div[name=sorter][data-number=0]')[0]
let filtersSection = $('div[id="filters-section"]')[0]
let sortersSection = $('div[id="sorters-section"]')[0]
let fsSection = $('#filters-sorters-section')

let addNewFilterDom = $('div[name="add-new-filter')[0]
let clearFilterDom = $('div[name="clear-filter"]')[0]
let clearAllFilterDom = $('div[name="clear-all-filter"]')[0]

let addNewSorterDom = $('div[name="add-new-sorter"]')[0]
let clearSorterDom = $('div[name="clear-sorter"]')[0]
let clearAllSorterDom = $('div[name="clear-all-sorter"]')[0]

let sendFilterDom = $('div[name="send-all-filter-sorter"]')[0]
let showMoreDom = $('div[id="show-more"]')[0]

let searchBox = $('#search-box')[0]
let searchButton = $('[data-trigger="search-button"]')[0]
let clearSearch = $('[data-trigger="clear-search"]')[0]
let shuffleButton = $('[data-trigger="shuffle"]')[0]
let toggleFiltersDom = $('[data-trigger="toggle-filters"]')[0]

let collectDom = $('[name="collect"]')[0]
let divederRow = document.querySelector('[name="divider-row"]')

// Define functions

const csrftoken = getCookie('csrftoken');

function clearDIners(){
    diners.innerHTML = dinersHtml
}

function renderDinerInfo(dinerInfo, dinerNode, source){
    let title = dinerInfo['title_'.concat(source)]
    let image = dinerInfo['image_'.concat(source)]
    let rating = dinerInfo['rating_'.concat(source)]
    let viewCount = dinerInfo['view_count_'.concat(source)]
    let link = dinerInfo['link_'.concat(source)]
    let redirectUrl = dinerInfo['redirect_url']
    let titleNode = dinerNode.querySelector('.title_'.concat(source))
    titleNode.innerText = title
    let imageNode = dinerNode.querySelector('.image_'.concat(source))
    imageNode.setAttribute('src', image)
    dinerNode.querySelector('.rating_value_'.concat(source)).innerText = rating
    dinerNode.querySelector('.view_count_value_'.concat(source)).innerText = viewCount
    dinerNode.querySelector('#link_'.concat(source)).setAttribute('href', link)
    let redirectHrefNode = dinerNode.querySelectorAll('.redirect-href_'.concat(source))
    for (let i = 0; i < redirectHrefNode.length; i++){
        redirectHrefNode[i].setAttribute('href', redirectUrl)
    }
    return dinerNode
}

function removeInfo(dinerNode, source){
    if (source != 'gm'){
        let titleDom = dinerNode.querySelector('.redirect-href_'.concat(source))
        titleDom.remove()
    }
    let infoRow = dinerNode.querySelector('.info_'.concat(source))
    infoRow.remove()
}

function renderGM(dinerInfo, dinerNode, source){
    let rating = dinerInfo['rating_'.concat(source)]
    let viewCount = dinerInfo['view_count_'.concat(source)]
    let link = dinerInfo['link_'.concat(source)]
    dinerNode.querySelector('.rating_value_'.concat(source)).innerText = rating
    dinerNode.querySelector('.view_count_value_'.concat(source)).innerText = viewCount
    dinerNode.querySelector('#link_'.concat(source)).setAttribute('href', link)
}

function renderDiner(diner){
    let dinerNode = dinerTemplate.cloneNode(true)
    let collectNode = dinerNode.querySelector('[name=collect].icon')
    collectNode.setAttribute('data-favorite', 0)
    let diner_uuid_ue = diner['uuid_ue']
    let diner_uuid_fp = diner['uuid_fp']
    let diner_uuid_gm = diner['uuid_gm']
    let redirectUrl = dinerInfoRoute.concat('?uuid_ue=').concat(diner_uuid_ue).concat('&uuid_fp=').concat(diner_uuid_fp)
    let diner_info_ue = false
    let diner_info_fp = false
    let diner_favorite = diner['favorite']
    let titleUe = dinerNode.querySelector('.title_ue')
    let titleFp = dinerNode.querySelector('.title_fp')
    let imageNodeFp = dinerNode.querySelector('.image_fp')
    let imageNodeUe = dinerNode.querySelector('.image_ue')
    
    imageNodeFp.setAttribute('src', '')
    imageNodeUe.setAttribute('src', '')
    
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
        renderDinerInfo(diner_info_ue, dinerNode, 'ue')
        collectNode.setAttribute('data-uuid-ue', diner_uuid_ue)
        if (diner_favorite){ 
            collectNode.setAttribute('data-favorite', 1)
            collectNode.setAttribute('src', "https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/heart_filled.svg")
        }
    } else{
        removeInfo(dinerNode, 'ue')
    }
    if (diner_uuid_fp != ''){
        diner_info_fp = {
            "title_fp": diner['title_fp'],
            "rating_fp": diner['rating_fp'],
            "view_count_fp": diner['view_count_fp'],
            "budget_fp": diner['budget_fp'],
            "image_fp": diner["image_fp"],
            "link_fp": diner["link_fp"],
            "redirect_url": redirectUrl
        }
        renderDinerInfo(diner_info_fp, dinerNode, 'fp')
        collectNode.setAttribute('data-uuid-fp', diner_uuid_fp)
        if (diner_favorite){
            collectNode.setAttribute('data-favorite', 1)
            collectNode.setAttribute('src', "https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/heart_filled.svg")
        }
    } else{
        removeInfo(dinerNode, 'fp')
    }
    if (diner_uuid_gm){
        diner_info_gm = {
            "rating_gm": diner['rating_gm'],
            "view_count_gm": diner['view_count_gm'],
            "link_gm": diner["link_gm"]
        }
        renderGM(diner_info_gm, dinerNode, 'gm')
    } else{
        removeInfo(dinerNode, 'gm')
    }
    if (diner_favorite){collectNode.setAttribute('data-favorite', 1)}
    else {collectNode.setAttribute('data-favorite', 0)}

    if ((imageNodeUe.getAttribute('src')) && (imageNodeFp.getAttribute('src'))){
        imageNodeFp.remove()
        titleFp.remove()
    } else if (imageNodeFp.getAttribute('src') == ""){
        imageNodeFp.remove()
        titleFp.remove()
    } else if (imageNodeUe.getAttribute('src') == ""){
        imageNodeUe.remove()
        titleUe.remove()
    }
    collectNode.addEventListener('click', (e)=>{
        let favorited = parseInt(e.target.getAttribute('data-favorite'))
        let activate = 0
        if (favorited == 0){activate = 1}
        let uuid_ue = e.target.getAttribute('data-uuid-ue')
        let uuid_fp = e.target.getAttribute('data-uuid-fp')
        if (uuid_ue && uuid_fp){changeFavorites(uuid_ue, uuid_fp, activate)}
        else if (uuid_fp){changeFavorites('', uuid_fp, activate)}
        else if (uuid_ue){changeFavorites(uuid_ue, '', activate)}
        if (activate == 1){
            e.target.setAttribute('data-favorite', 1)
            e.target.setAttribute('src', "https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/heart_filled.svg")
        }
        if (activate == 0){
            e.target.setAttribute('data-favorite', 0)
            e.target.setAttribute('src', "https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/heart.svg")
        }
    })
    return dinerNode
}

function renderList(data){
    let results = data.data
    for (let i = 0; i < results.length; i++){
        let diner = results[i]
        let newDividerRow = divederRow.cloneNode(true)
        diner = renderDiner(diner)
        diners.appendChild(diner)
        diners.appendChild(newDividerRow)
        $(newDividerRow).show()
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
    window.scrollTo(0,(document.body.scrollHeight - window.innerHeight));
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
    removeButton.innerHTML = `<img class="button-smaller" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/filter_wide.svg" data-number=${newFilterNumber}><img class="button-smaller" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/remove_filter.svg" data-number=${newFilterNumber}>`
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
    clearFilter(clearFilterDom)
    let removeFilters = $('[class*="remove-filter"]')
    for( let i = 0; i < removeFilters.length; i ++){
        removeFilter(removeFilters[i])
    }
}

function renderOptions(data){
    let tagsUe = data.data['tags_ue']
    let tagsFp = data.data['tags_fp']
    let filterValue0 =  $('div[name="filter-value"][data-number="0"]')[0]
    let tagsSelectUe = $(filterValue0).find(".tags_ue")[0]
    let tagsSelectFp = $(filterValue0).find(".tags_fp")[0]
    for (let r = 0; r < tagsUe.length; r++){
        let optionValueUe = tagsUe[r]
        let optionUe = document.createElement('option')
        optionUe.value =  optionValueUe
        optionUe.setAttribute('data-type', typeof optionValueUe)
        optionUe.innerText = optionValueUe
        tagsSelectUe.appendChild(optionUe)
    }
    for (let i=0; i < tagsFp.length; i++){
        let optionValueFp = tagsFp[i]
        let optionFp = document.createElement('option')
        optionFp.value =  optionValueFp
        optionFp.setAttribute('data-type', typeof optionValueFp)
        optionFp.innerText = optionValueFp
        tagsSelectFp.appendChild(optionFp)
    }
}

function renderFilter(dataNumber){
    let eachFilterSource = $(`select[name="filter-source"][data-number=${dataNumber}]`)
    let eachFilterType =  $(`select[name="filter-type"][data-number=${dataNumber}]`)
    let eachFilterOperator = $(`select[name="filter-operator"][data-number=${dataNumber}]`)
    let eachFilterValue =  $(`select[name="filter-value"][data-number=${dataNumber}]`)
    
    $(eachFilterType).hide()
    $(eachFilterType[0]).show().prop('disabled', 'disabled')
    
    $(eachFilterOperator).hide();
    $(eachFilterOperator[0]).show().prop('disabled', 'disabled')
    
    $(eachFilterValue).hide()
    $(eachFilterValue[0]).show().prop('disabled', 'disabled')

    if (eachFilterSource.val() =='ue'){eachFilterSource.attr('data-source-css', 'ue')}
    else if (eachFilterSource.val() =='fp'){eachFilterSource.attr('data-source-css', 'fp')}

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
    removeButton.innerHTML = `<img class="button-smaller" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/sorter_wide.svg" data-number=${newSorterNumber}><img class="button-smaller" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/remove_sorter.svg" data-number=${newSorterNumber}>`
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
    let selects = $(sorters).find(`select[data-number=${dataNumber}]`)
    for (let i = 0; i < selects.length; i++){
        selects[i].value = 'default'
        if (selects[i].getAttribute('name') != 'sorter-source'){
            $(selects[i]).prop('disabled', 'disabled')
        }
    }
}


function clearAllSorter(){
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
    
    $(eachSorterType).hide()
    $(eachSorterType[0]).show().prop('disabled', 'disabled')
    
    $(eachSorterOperator).hide()
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

function search(offset, showMore=false){
    showLoading()
    $(showMoreDom).hide()
    let keyWord = document.getElementById('search-box')
    let filterSet = $('div[name="filter"]')
    let sorterSet = $('div[name="sorter"]')
    conditions = createConditions($(keyWord).val())
    conditions = turnFIltersToConditions(conditions, filterSet)
    conditions = turnSortersToConditions(conditions, sorterSet)
    data = {'condition': conditions, 'offset': offset}
    console.log(conditions)
    if (showMore){
        let height = $(document).height()
        ajaxPost(dinerSearchAPI, data, function(response){
            renderList(response)
            window.scrollTo(0,(height - (200)));
            endLoading()
        })
    }
    else {
        ajaxPost(dinerSearchAPI, data, function(response){
            clearDIners()
            renderList(response)
            endLoading()
        })
    }
    Cookies.set('ufc_condition', JSON.stringify(conditions))
    Cookies.set('ufc_offset', JSON.stringify(offset))
}

function turnCookieToJson(name){
    let cookieStr = getCookie(name)
    let jsonObject = JSON.parse(cookieStr)
    return jsonObject
}

function bringConditionBack(){
    let keys = Object.keys(Cookies.get())
    let conditions = false
    let ufc_offset = 0
    let filtersExist = false
    let sortersExist = false
    let keywordExist = false
    if (keys.includes('ufc_condition')){conditions = turnCookieToJson('ufc_condition')}
    if (keys.includes('ufc_offset')){ufc_offset = parseInt(turnCookieToJson('ufc_offset'))}
    if (conditions){
        let conditionsKeys = Object.keys(conditions)
        if (conditionsKeys.includes('filter')){
            filtersExist = bringFiltersBack(conditions.filter)
        }
        if (conditionsKeys.includes('sorter')){
            sortersExist = bringSortersBack(conditions.sorter)
        }
        if (conditionsKeys.includes('keyword')){
            keywordExist = bringKeywordBack(conditions.keyword)
            console.log(conditions.keyword)
        }
    }
    if (ufc_offset > 0){
        console.log('a')
    }
    if ((filtersExist) || (sortersExist) || (keywordExist)){
        search(ufc_offset)
        $(fsSection).show()
    } else {
        $(fsSection).hide()
        ajaxPost(dinerSearchAPI, initData, function(response){
            renderList(response)
            endLoading()
        })
    }
}

function bringFiltersBack(cookieFilters){
    let realFilters = []
    for (let i=0; i<cookieFilters.length; i++){
        let filter = cookieFilters[i]
        if ((filter.field == 'default') || (filter.filter == 'default') || (filter.value == null) ){ console.log('default filter')}
        else{realFilters.push(filter)}
    }
    for (let i=1; i<realFilters.length; i++){
        appendFilter()
    }
    for (let i=0; i<realFilters.length; i++){
        let filter = realFilters[i]
        let sourceArray = filter.field.split('_')
        let source = sourceArray[sourceArray.length - 1]
        let filterSource = document.querySelector(`[name="filter-source"][data-number="${i}"]`)
        filterSource.value = source
        let filterType = document.querySelector(`[name="filter-type"][data-number="${i}"][class*="${source}"]`)
        filterType.value=filter.field
        
        let filterOperator = document.querySelector(`[name="filter-operator"][data-number="${i}"][class*="${filter.field}"]`)
        filterOperator.value=filter.filter
        
        let filterValue = document.querySelector(`[name="filter-value"][data-number="${i}"][class*="${filter.field}"]`)
        filterValue.value=filter.value.toString()
        renderFilter(i)
    }
    if (realFilters.length > 0){return true}
    else {return false}
}

function bringSortersBack(cookieSorters){
    let realSorters = []
    for (let i=0; i<cookieSorters.length; i++){
        let sorter = cookieSorters[i]
        if ((sorter.field == 'default') || (sorter.sorter == 'default')){ console.log('default sorter')}
        else{realSorters.push(sorter)}
    }
    for (let i=1; i<realSorters.length; i++){
        appendSorter()
    }
    for (let i=0; i<realSorters.length; i++){
        let sorter = realSorters[i]
        let sourceArray = sorter.field.split('_')
        let source = sourceArray[sourceArray.length - 1]
        let sorterSource = document.querySelector(`[name="sorter-source"][data-number="${i}"]`)
        sorterSource.value = source
        let sorterType = document.querySelector(`[name="sorter-type"][data-number="${i}"][class*="${source}"]`)
        sorterType.value=sorter.field
        
        let sorterOperator = document.querySelector(`[name="sorter-operator"][data-number="${i}"][class*="${sorter.field}"]`)
        sorterOperator.value=sorter.sorter
        renderSorter(i)
    }
    if (realSorters.length > 0){return true}
    else {return false}
}

function bringKeywordBack(cookieKeyword){
    let keyword = cookieKeyword
    document.getElementById('search-box').value = keyword
    return true
}

function shuffle(){
    showLoading()
    data = {}
    ajaxPost(dinerShuffleAPI, data, function(response){
        renderList(response)
        endLoading()
    })
}

function changeFavorites(uuid_ue, uuid_fp, activate){
    let data = {
        'uuid_ue': uuid_ue,
        'uuid_fp': uuid_fp,
        'activate': activate
    }
    ajaxPost(favoritesAPI, data, console.log)
}

// start to render
showLoading()

ajaxGet(filtersAPI, function(response){
    renderFilters();
    renderOptions(response);
    bringConditionBack()
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
    $(fsSection).toggle()
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
    search(0)
})

$(searchButton).click(function(){
    clearDIners()
    search(0)
})

$(searchBox).keydown(function(e){
    if (e.keyCode == 13){
        clearDIners()
        search(0)
    }
})

$(shuffleButton).click(function(){
    clearDIners()
    $(showMoreDom).hide()
    $(fsSection).hide()
    shuffle()
})

$(showMoreDom).click(function(){
    let offset = parseInt(showMoreDom.getAttribute('data-offset'))
    search(offset, true)
})

