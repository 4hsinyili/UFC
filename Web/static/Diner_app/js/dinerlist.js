// API related variables
const filtersAPI = 'api/v1/filters'
const dinerSearchAPI = 'api/v1/dinersearch'
const dinerShuffleAPI = 'api/v1/dinershuffle'
const favoritesAPI = 'api/v1/favorites'

const domain = window.location.origin
const dinerInfoRoute = domain.concat('/dinerinfo')

const initData = {'condition': {}, 'offset': 0}

// Doms
const diners = document.getElementById('diners')
const filters = document.getElementById('filters')
const sorters = document.getElementById('sorters')
const dinerTemplate = document.getElementById('diner-template')
const dinersHtml = diners.innerHTML

const firstFilter = document.querySelector('div[name="filter"][data-number="0"]')
const firstSorter = document.querySelector('div[name="sorter"][data-number="0"]')
const fsSection = document.querySelector('#filters-sorters-section')

const addNewFilterDom = document.querySelector('div[name="add-new-filter"]')
const clearFilterDom = document.querySelector('div[name="clear-filter"]')
const clearAllFilterDom = document.querySelector('div[name="clear-all-filter"]')

const addNewSorterDom = document.querySelector('div[name="add-new-sorter"]')
const clearSorterDom = document.querySelector('div[name="clear-sorter"]')
const clearAllSorterDom = document.querySelector('div[name="clear-all-sorter"]')

const sendFilterDom = document.querySelector('div[name="send-all-filter-sorter"]')
const showMoreDom = document.querySelector('div[id="show-more"]')

const searchBox = document.getElementById('search-box')
const searchButton = document.querySelector('[data-trigger="search-button"]')
const clearSearch = document.querySelector('[data-trigger="clear-search"]')
const shuffleButton = document.querySelector('[data-trigger="shuffle"]')
const toggleFiltersDom = document.querySelector('[data-trigger="toggle-filters"]')

const divederRow = document.querySelector('[name="divider-row"]')

// Define functions

const csrftoken = getCookie('csrftoken');

function clearDIners(){
    diners.innerHTML = dinersHtml
}

function createConditions(keyWord){
    let conditions = {}
    if (keyWord){conditions['keyword'] = keyWord}
    return conditions
}

function appendFilter(){
    let filterArray = $('div[name="filter"]')
    let newFilter = firstFilter.cloneNode(true)
    $(newFilter).show()

    let newNumber = filterArray.length
    newFilter.setAttribute('data-number', newNumber)
    let children = $(newFilter).find("[data-number]")
    newFilter.setAttribute('data-number', newNumber)
    for (let child of  children){
        child.setAttribute('data-number', newNumber)
    }
    
    filters.appendChild(newFilter)
    let removeButton = document.querySelector(`[name="clear-filter"][data-number="${newNumber}"]`)
    removeButton.classList.add('remove-filter')
    removeButton.innerHTML = `<img class="button-smaller" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/filter_wide.svg" data-number=${newNumber}><img class="button-smaller" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/remove_filter.svg" data-number=${newNumber}>`
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
    let firstValueFilter =  $('div[name="filter-value"][data-number="0"]')[0]
    let tagsSelectUe = $(firstValueFilter).find(".tags_ue")[0]
    let tagsSelectFp = $(firstValueFilter).find(".tags_fp")[0]
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
    let sourceFilter = $(`select[name="filter-source"][data-number=${dataNumber}]`)
    let typeFilter =  $(`select[name="filter-type"][data-number=${dataNumber}]`)
    let operatorFilter = $(`select[name="filter-operator"][data-number=${dataNumber}]`)
    let valueFilter =  $(`select[name="filter-value"][data-number=${dataNumber}]`)
    
    $(typeFilter).hide()
    $(typeFilter[0]).show().prop('disabled', 'disabled')
    
    $(operatorFilter).hide();
    $(operatorFilter[0]).show().prop('disabled', 'disabled')
    
    $(valueFilter).hide()
    $(valueFilter[0]).show().prop('disabled', 'disabled')

    if (sourceFilter.val() =='ue'){sourceFilter.attr('data-source-css', 'ue')}
    else if (sourceFilter.val() =='fp'){sourceFilter.attr('data-source-css', 'fp')}
    else if (sourceFilter.val() =='gm'){sourceFilter.attr('data-source-css', 'gm')}

    let chosedType = $(`select[name*="filter-type"][data-number=${dataNumber}][class*="${sourceFilter.val()}"]`)
    if (chosedType.length == 1){
        $(typeFilter[0]).hide()
        $(chosedType).show().prop('disabled', false)
    };
    let chosedOperator = $(`select[name="filter-operator"][data-number=${dataNumber}].${chosedType.val()}.${sourceFilter.val()}`)
    if (chosedOperator.length == 1){
        $(operatorFilter[0]).hide()
        $(chosedOperator).show().prop('disabled', false)
    };
    let chosedValue = $(`select[name="filter-value"][data-number=${dataNumber}].${chosedType.val()}.${sourceFilter.val()}`);
    if (chosedValue.length == 1){
        $(valueFilter[0]).hide()
        $(chosedValue).show().prop('disabled', false)
    };
}

function renderFilters(){
    let filterArray = $('div[name="filter"]')
    let filterSetLength = filterArray.length
    for (let i = 0; i < filterSetLength; i++){
        renderFilter(i)
    };
}

function turnFIltersToConditions(conditions, filterArray){
    conditions['filter'] = []
    for (let filter of filterArray){
        tFSelects = $(filter).find('select')
        conditions['filter'].push({})
        let last = conditions['filter'].length - 1

        for (let tFSelect of tFSelects){

            if ($(tFSelect).css('display') != 'none'){

                if (tFSelect.getAttribute('name') == 'filter-type'){
                    conditions['filter'][last]['field'] = $(tFSelect).val()
                } else if (tFSelect.getAttribute('name') == 'filter-operator'){
                    conditions['filter'][last]['filter'] = $(tFSelect).val()
                }else if  (tFSelect.getAttribute('name') == 'filter-value'){

                    if (tFSelect.getAttribute('data-type') == 'number'){
                        conditions['filter'][last]['value'] = parseInt($(tFSelect).val())
                    } else if (tFSelect.getAttribute('data-type') == 'string'){
                        conditions['filter'][last]['value'] = $(tFSelect).val()
                    } else if (tFSelect.getAttribute('data-type') == 'float'){
                        conditions['filter'][last]['value'] = parseFloat($(tFSelect).val())
                    }
                }
            }
        }
    }
    return conditions
}

function appendSorter(){
    let sorterArray = $('div[name="sorter"]')
    let newSorter = firstSorter.cloneNode(true)
    $(newSorter).show()

    let newNumber = sorterArray.length
    newSorter.setAttribute('data-number', newNumber)
    let children = $(newSorter).find("[data-number]")
    newSorter.setAttribute('data-number', newNumber)
    for (let child of children){
        child.setAttribute('data-number', newNumber)
    }
    sorters.appendChild(newSorter)
    let removeButton = document.querySelector(`[name="clear-sorter"][data-number="${newNumber}"]`)
    removeButton.classList.add('remove-sorter')
    removeButton.innerHTML = `<img class="button-smaller" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/sorter_wide.svg" data-number=${newNumber}><img class="button-smaller" src="https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/remove_sorter.svg" data-number=${newNumber}>`
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
    let sourceSorter = $(`select[name="sorter-source"][data-number=${dataNumber}]`)
    let typeSorter =  $(`select[name="sorter-type"][data-number=${dataNumber}]`)
    let operatorSorter = $(`select[name="sorter-operator"][data-number=${dataNumber}]`)
    
    $(typeSorter).hide()
    $(typeSorter[0]).show().prop('disabled', 'disabled')
    
    $(operatorSorter).hide()
    $(operatorSorter[0]).show().prop('disabled', 'disabled')

    if (sourceSorter.val() =='ue'){sourceSorter.attr('data-source-css', 'ue')}
    else if (sourceSorter.val() =='fp'){sourceSorter.attr('data-source-css', 'fp')}
    else if (sourceSorter.val() =='gm'){sourceSorter.attr('data-source-css', 'gm')}

    let chosedSorterType = $(`select[name*="sorter-type"][data-number=${dataNumber}][class*="${sourceSorter.val()}"]`)
    if (chosedSorterType.length == 1){
        $(typeSorter[0]).hide()
        $(chosedSorterType).show().prop('disabled', false)
    };

    let chosedSorterOperator = $(`select[name="sorter-operator"][data-number=${dataNumber}].${chosedSorterType.val()}.${sourceSorter.val()}`)
    if (chosedSorterOperator.length == 1){
        $(operatorSorter[0]).hide()
        $(chosedSorterOperator).show().prop('disabled', false)
    };
}

function renderSorters(){
    let sorterArray = $('div[name="sorter"]')
    let sorterSetLength = sorterArray.length
    for (let i = 0; i < sorterSetLength; i++){
        renderSorter(i)
    };
}

function turnSortersToConditions(conditions, sorterArray){
    conditions['sorter'] = []

    for (let sorter of sorterArray){
        tFSelects = $(sorter).find('select')
        conditions['sorter'].push({})
        let last = conditions['sorter'].length - 1

        for (let tFSelect of tFSelects){

            if ($(tFSelect).css('display') != 'none'){

                if (tFSelect.getAttribute('name') == 'sorter-type'){
                    conditions['sorter'][last]['field'] = $(tFSelect).val()
                } else if (tFSelect.getAttribute('name') == 'sorter-operator'){
                    conditions['sorter'][last]['sorter'] = parseInt($(tFSelect).val())
                }
            }
        }
    }
    return conditions
}

function search(offset=0, showMore=false){
    showLoading()
    $(showMoreDom).hide()
    let keyWord = document.getElementById('search-box')
    let filterArray = $('div[name="filter"]')
    let sorterArray = $('div[name="sorter"]')
    conditions = createConditions($(keyWord).val())
    conditions = turnFIltersToConditions(conditions, filterArray)
    conditions = turnSortersToConditions(conditions, sorterArray)
    data = {'condition': conditions, 'offset': offset}
    if (showMore){
        let height = $(document).height()
        ajaxPost(dinerSearchAPI, data, function(response){
            result = renderList(response)
            window.scrollTo(0,(height - (200)));
            endLoading()
            if (!result){
                noData()
            }
        })
    }
    else {
        ajaxPost(dinerSearchAPI, data, function(response){
            clearDIners()
            result = renderList(response)
            endLoading()
            if (!result){
                noData()
            }
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
        }
    }
    if (ufc_offset > 0){
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
        if ((filter.field == 'default') || (filter.filter == 'default') || (filter.value == null) ){}
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
        if ((sorter.field == 'default') || (sorter.sorter == 'default')){}
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
    search()
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
    search()
})

$(sendFilterDom).click(function(){
    clearDIners()
    search()
})

$(searchButton).click(function(){
    clearDIners()
    search()
})

$(searchBox).keydown(function(e){
    if (e.keyCode == 13){
        clearDIners()
        search()
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


clearSearch.click(function(){
    searchBox.val() = ''
})