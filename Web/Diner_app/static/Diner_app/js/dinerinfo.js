const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const dinerID = urlParams.get('diner_id')
let dinerInfoAPI = 'api/v1/dinerinfo'.concat('?diner_id=').concat(dinerID)

let dinerTitleDom = document.getElementById('diner-title')
let dinerImageDom = document.getElementById('diner-image')
let dinerGPSDom = document.getElementById('diner-gps')
let dinerAddressDom = document.getElementById('diner-address')
let dinerRatingDom = document.getElementById('ue-rating')
let dinerViewCountDom = document.getElementById('ue-view_count')
let dinerBudgetDom = document.getElementById('ue-budget')
let dinerLinkDom = document.getElementById('ue-link')
let dinerDeliverFeeDom = document.getElementById('ue-deliver_fee')
let dinerDeliverTimeDom = document.getElementById('ue-deliver_time')
let dinerOpenHoursDom = document.getElementById('ue-open_hours')
let dinerMenuDom = document.getElementById('ue-menu')
let dinerSection = document.querySelector('[name=section]')
let dinerSections = document.querySelector('[name=sections]')
let dinerSubsection = document.querySelector('[name=subsection]')
let dinerItems = document.querySelector('[name=items]')
let dinerItem = document.querySelector('[name=item]')
let openHourDom = document.querySelector('[name=open-hour]')
let openHoursDom = document.querySelector('#ue-open_hours')

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

ajaxGet(dinerInfoAPI, function(response){
    renderDiner(response)
})

function renderDiner(response){
    let data = response.data
    console.log(data)
    dinerTitleDom.innerText = data.title
    dinerImageDom.setAttribute('src', data.image)
    dinerRatingDom.innerText = 'ue rating: '.concat(data.rating)
    dinerViewCountDom.innerText = 'ue view_count: '.concat(data.view_count)
    dinerBudgetDom.innerText = 'ue budget: '.concat('$'.repeat(data.budget))
    dinerLinkDom.innerText = 'ue link: '.concat(data.link)
    dinerDeliverFeeDom.innerText = 'ue deliver_fee: '.concat(data.deliver_fee)
    dinerDeliverTimeDom.innerText = 'ue deliver_time: '.concat(data.deliver_time)
    renderOpenHours(data)
    let pivotMenuResults = pivotMenu(data)
    let sections = pivotMenuResults[0]
    let subsectionTitles = pivotMenuResults[1]
    renderMenu(sections, subsectionTitles)
}

function renderOpenHours(data){
    let openHours = data.open_hours
    for (let i=0; i < openHours.length; i++){
        let newOpenHour = openHourDom.cloneNode(true)
        newOpenHour.innerText = openHours[i]
        $(newOpenHour).show()
        openHoursDom.appendChild(newOpenHour)
    }
}

function pivotMenu(data){
    let sectionTitleDom = dinerMenuDom.querySelector('[name=section-title]')
    let subsectionTitleDom = dinerMenuDom.querySelector('[name=subsection-title]')
    let itemsDom = dinerMenuDom.querySelector('[name=items')
    let itemDom = dinerMenuDom.querySelector('[name=item')
    let menus = data.menu
    let sectionTitlesSet = new Set()
    let sections = new Object()
    let subsectionTitleSet = new Array()
    for (let i=0; i < menus.length; i++){
        let menu = menus[i]
        let sectionTitle = menu.section_title
        sectionTitlesSet.add(sectionTitle)
    }
    let sectionTitles = Array.from(sectionTitlesSet)
    console.log(sectionTitles)
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

function renderMenu(sections, subsectionTitles){
    console.log(sections)
    let keys = Object.keys(sections)
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
        $(newSection).show()
        dinerSections.appendChild(newSection)
    }
}