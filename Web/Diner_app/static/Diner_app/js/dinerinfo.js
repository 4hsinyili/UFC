const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const uuidUE = urlParams.get('uuid_ue')
const uuidFP = urlParams.get('uuid_fp')
let dinerInfoAPI = 'api/v1/dinerinfo'.concat('?uuid_ue=').concat(uuidUE).concat('&uuid_fp=').concat(uuidFP)

let dinerSection = document.querySelector('[name=section]')
let dinerSubsection = document.querySelector('[name=subsection]')
let dinerItems = document.querySelector('[name=items]')
let dinerItem = document.querySelector('[name=item]')
let tabDom = document.querySelector('[name=section-tab]')
let tabPkDom = document.querySelector('[name=section-tab-pk]')

$('#diner-info').hide()

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

function renderDiner(response, source){
    let diner = response.data
    renderTitle(diner, source)
    renderImage(diner, source)
    renderRating(diner, source)
    renderViewCount(diner, source)
    renderBudget(diner, source)
    renderDeliverFee(diner, source)
    renderDeliverTime(diner,source)
    renderOpenHours(diner, source)
    let pivotMenuResults = pivotMenu(diner, source)
    let sections = pivotMenuResults[0]
    let subsectionTitles = pivotMenuResults[1]
    renderMenu(sections, subsectionTitles, source)
}

function renderTitle(diner, source){
    let selector = 'title_'.concat(source)
    let titleDom = document.getElementById(selector)
    titleDom.innerText = diner['title_'.concat(source)]
    titleDom.setAttribute('href', diner['link_'.concat(source)])
    return titleDom
}

function renderImage(diner, source){
    let selector = 'image_'.concat(source)
    let imageDom = document.getElementById(selector)
    imageDom.setAttribute('src', diner['image_'.concat(source)])
    return imageDom
}

function renderRating(diner, source){
    let selector = 'rating_'.concat(source)
    let ratingDom = document.getElementById(selector)
    ratingDom.innerText = `${source} rating: `.concat(diner['rating_'.concat(source)])
    return ratingDom
}

function renderViewCount(diner, source){
    let selector = 'view_count_'.concat(source)
    let viewCountDom = document.getElementById(selector)
    viewCountDom.innerText = `${source} view_count: `.concat(diner['view_count_'.concat(source)])
    return viewCountDom
}

function renderBudget(diner, source){
    let selector = 'budget_'.concat(source)
    let budgetDom = document.getElementById(selector)
    budgetDom.innerText = `${source} budget: `.concat('$'.repeat(diner['budget_'.concat(source)]))
    return budgetDom
}

function renderDeliverFee(diner, source){
    let selector = 'deliver_fee_'.concat(source)
    let deliverFeeDom = document.getElementById(selector)
    deliverFeeDom.innerText = `${source} deliver_fee: `.concat(diner['deliver_fee_'.concat(source)])
    return deliverFeeDom
}

function renderDeliverTime(diner, source){
    let selector = 'deliver_time_'.concat(source)
    let deliverTimeDom = document.getElementById(selector)
    deliverTimeDom.innerText = `${source} deliver_time: `.concat(diner['deliver_time_'.concat(source)])
    return deliverTimeDom
}


function renderOpenHours(diner, source){
    let openHoursDomSelector = 'open_hours_'.concat(source)
    let openHoursDom = document.getElementById(openHoursDomSelector)
    let openHours = diner['open_hours_'.concat(source)]
    let openHourDomSelector = `[name=open_hour_${source}]`
    let openHourDom = document.querySelector(openHourDomSelector)
    for (let i=0; i < openHours.length; i++){
        let newOpenHour = openHourDom.cloneNode(true)
        newOpenHour.innerText = openHours[i]
        $(newOpenHour).show()
        openHoursDom.appendChild(newOpenHour)
    }
}

function pivotMenu(diner,source){
    let menus = diner['menu_'.concat(source)]
    let sectionTitlesSet = new Set()
    let sections = new Object()
    let subsectionTitleSet = new Array()
    for (let i=0; i < menus.length; i++){
        let menu = menus[i]
        let sectionTitle = menu.section_title
        sectionTitlesSet.add(sectionTitle)
    }
    let sectionTitles = Array.from(sectionTitlesSet)
    for (let i=0; i < sectionTitles.length; i++){
        let sectionTitle = sectionTitles[i]
        sections[sectionTitle] = []
    }
    for (let i=0; i < menus.length; i++){
        let menu = menus[i]
        let sectionTitle = menu.section_title
        let subsectionTitle = menu.subsection_title
        subsectionTitleSet.push(subsectionTitle)
        let items = {
            'subsection_title': subsectionTitle,
            'items': menu.items
        }
        sections[sectionTitle].push(items)
    }
    return [sections, subsectionTitleSet]
}

function renderMenu(sections, subsectionTitles, source){
    console.log(sections)
    let keys = Object.keys(sections)
    let menuSectionsDom = document.querySelector(`[name=sections_${source}]`)
    let tabsDom = document.getElementById(`section-tabs_${source}`)
    let menuPkSectionsDom = document.querySelector(`[name=sections_pk_${source}]`)
    let tabsPkDom = document.getElementById(`section-tabs_pk_${source}`)
    for (let i=0; i < keys.length; i++){
        let key = keys[i]
        let subsections = sections[key]
        let newSection = dinerSection.cloneNode(true)
        let nsTitleDom = newSection.querySelector('[name=section-title]')
        nsTitleDom.innerText = key
        for (let r=0; r < subsections.length; r++){
            let subsection = subsections[r]
            let items = subsection.items
            let newSubsection = dinerSubsection.cloneNode(true)
            let subsctionTitle = subsection.subsection_title
            let subsectionTitleDom = newSubsection.querySelector('[name=subsection-title]')
            let newItemsDom = dinerItems.cloneNode(true)
            subsectionTitleDom.innerText = subsctionTitle
            for (let z=0; z < items.length; z++){
                let item = items[z]
                let newItem = dinerItem.cloneNode(true)
                let itemTitle = item.item_title
                let itemDescription = item.item_description
                let itemPrice = item.item_price
                let itemImage = item.item_image_url
                let titleDom = newItem.querySelector('[name=item-title]')
                let priceDom = newItem.querySelector('[name=item-price]')
                let imageDom = newItem.querySelector('[name=item-image]')
                let descriptionDom = newItem.querySelector('[name=item-description]')
                titleDom.innerText = itemTitle
                priceDom.innerText = itemPrice
                imageDom.setAttribute('src', itemImage)
                descriptionDom.innerText = itemDescription
                $(newItem).show()
                newItemsDom.appendChild(newItem)
            }
            $(newItemsDom).show()
            newSubsection.appendChild(newItemsDom)
            $(newSubsection).show()
            newSection.appendChild(newSubsection)
        }
        
        
        let newTabDom = tabDom.cloneNode(true)
        newTabDom.innerText = key
        $(newTabDom).show()
        let newPkTabDom = tabPkDom.cloneNode(true)
        newPkTabDom.innerText = key
        tabsDom.appendChild(newTabDom)
        let newPkSection = newSection.cloneNode(true)
        newSection.setAttribute('data-section-title', key)
        $(newSection).show()
        menuSectionsDom.appendChild(newSection)

        if (uuidUE & uuidFP){
            $(newPkTabDom).show()
            tabsPkDom.appendChild(newPkTabDom)
            newPkSection.setAttribute('data-section-title-pk', key)
            menuPkSectionsDom.appendChild(newPkSection)
        }
    }
}

ajaxGet(dinerInfoAPI, function(response){
    if (uuidUE){
        renderDiner(response, 'ue')
        $('#info_ue').show()
    }
    if (uuidFP){
        renderDiner(response, 'fp')
        $('#info_fp').show()
    }
    $('#diner-info').show()
})

document.addEventListener('click', (e)=>{
    if (e.target.getAttribute('id') == 'show-more-info_ue'){
        $(e.target.parentNode.parentNode.parentNode.lastElementChild).toggle()
    } else if (e.target.getAttribute('id') == 'show-more-info_fp'){
        $(e.target.parentNode.parentNode.parentNode.lastElementChild).toggle()
    }
})

document.addEventListener('click', (e)=>{
    console.log('aa')
    if (e.target.getAttribute('name') == 'section-tab'){
        let dataSectionTitle = e.target.innerText
        $(`[data-section-title="${dataSectionTitle}"]`).toggle()
    } else if (e.target.getAttribute('name') == 'section-tab-pk'){
        let dataSectionTitle = e.target.innerText
        $(`[data-section-title-pk="${dataSectionTitle}"]`).toggle()
    }
})