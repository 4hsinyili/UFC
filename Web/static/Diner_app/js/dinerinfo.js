let queryString = window.location.search;
let urlParams = new URLSearchParams(queryString);
let uuidUE = urlParams.get('uuid_ue')
let uuidFP = urlParams.get('uuid_fp')
let dinerInfoAPI = 'api/v1/dinerinfo'.concat('?uuid_ue=').concat(uuidUE).concat('&uuid_fp=').concat(uuidFP)
let nqAPI = 'api/v1/noteq'

let dinerSection = document.querySelector('[name=section]')
let dinerSubsection = document.querySelector('[name=subsection]')
let dinerItems = document.querySelector('[name=items]')
let dinerItem = document.querySelector('[name=item]')
let tabDom = document.querySelector('[name=section-tab]')
let tabPkDom = document.querySelector('[name=section-tab-pk]')

let reportError = document.getElementById('report-error')

$('#diner-info').hide()

reportError.addEventListener('click', (e)=>{
    if (e.target.getAttribute('data-login') == "True"){
        let reContent = document.getElementById('report-error-content').cloneNode(true)
        Swal.fire({
            title: '回報方式',
            html: reContent,
            customClass: 'justify-content-center',
            showConfirmButton: false
        })
    } else {
        let reContent = document.getElementById('login-first').cloneNode(true)
        Swal.fire({
            title: '回報方式',
            html: reContent,
            customClass: 'justify-content-center'
        })
    }
})

const csrftoken = getCookie('csrftoken');

function renderDiner(response, source){
    let diner = response.data
    let titleDom = renderTitle(diner, source)
    let imageDom = renderImage(diner, source)
    let ratingDom = renderRating(diner, source)
    let viewCountDom = renderViewCount(diner, source)
    let deliverFeeDom = renderDeliverFee(diner, source)
    let deliverTimeDom = renderDeliverTime(diner,source)
    let openHoursDom = renderOpenHours(diner, source)
    let pivotMenuResults = pivotMenu(diner, source)
    let sections = pivotMenuResults[0]
    let subsectionTitles = pivotMenuResults[1]
    renderMenu(sections, source)
    renderColumnName(diner, source)
    return [titleDom, imageDom, ratingDom, viewCountDom, deliverFeeDom, deliverTimeDom, openHoursDom]
}

function renderGMInfo(response){
    let diner = response.data
    let ratingDom = renderRating(diner, 'gm')
    let viewCountDom = renderViewCount(diner, 'gm')
    renderColumnName(diner, 'gm')
}

function removeGM(){
    let columnNameDom = document.getElementById(`column_name_gm`)
    columnNameDom.remove()
    let ratingDom = document.getElementById(`rating_gm`)
    ratingDom.remove()
    let viewCountDom = document.getElementById(`view_count_gm`)
    viewCountDom.remove()
    let deliverFeeDom = document.getElementById('deliver_fee_gm')
    deliverFeeDom.remove()
    let showMoreDom = document.getElementById('show-more-info_gm')
    showMoreDom.remove()
    let deliverTimeDom = document.getElementById('deliver_time_gm')
    deliverTimeDom.remove()
}

function removeDiner(source){
    let titleDom = document.getElementById(`title_${source}`)
    titleDom.remove()
    let ratingDom = document.getElementById(`rating_${source}`)
    ratingDom.remove()
    let imageDom = document.getElementById(`image_${source}`)
    imageDom.remove()
    let viewCountDom = document.getElementById(`view_count_${source}`)
    viewCountDom.remove()
    let deliverFeeDom = document.getElementById(`deliver_fee_${source}`)
    deliverFeeDom.remove()
    let deliverTimeDom = document.getElementById(`deliver_time_${source}`)
    deliverTimeDom.remove()
    let openHoursDom = document.getElementById(`open_hours_${source}`)
    openHoursDom.remove()
    let menuDom = document.getElementById(`menu_${source}`)
    menuDom.remove()
    let infoColumnNameDom = document.getElementById(`column_name_${source}`)
    infoColumnNameDom.remove()
    let showMoreDom = document.getElementById(`show-more-info_${source}`)
    showMoreDom.remove()
    let dividerDom = document.getElementById(`divider_${source}`)
    dividerDom.remove()
    let detailDom = document.getElementById(`detail_${source}`)
    detailDom.remove()
}

function removePk(){
    document.getElementById('menu_pk').remove()
    $('[id^="cheaper-item_"]').remove()
}

function renderTitle(diner, source){
    let selector = 'title_'.concat(source)
    let titleDom = document.getElementById(selector)
    titleDom.innerText = diner['title_'.concat(source)]
    titleDom.setAttribute('href', diner['link_'.concat(source)])
    let webTitle = document.getElementById('web-title')
    webTitle.innerText = webTitle.innerText.concat(' | ').concat(diner['title_'.concat(source)])
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
    ratingDom.innerText = ratingDom.innerText.concat(diner['rating_'.concat(source)])
    return ratingDom
}

function renderViewCount(diner, source){
    let selector = 'view_count_'.concat(source)
    let viewCountDom = document.getElementById(selector)
    viewCountDom.innerText = viewCountDom.innerText.concat(diner['view_count_'.concat(source)])
    return viewCountDom
}

function renderBudget(diner, source){
    let selector = 'budget_'.concat(source)
    let budgetDom = document.getElementById(selector)
    budgetDom.innerText = budgetDom.innerText.concat('$'.repeat(diner['budget_'.concat(source)]))
    return budgetDom
}

function renderDeliverFee(diner, source){
    let selector = 'deliver_fee_'.concat(source)
    let deliverFeeDom = document.getElementById(selector)
    deliverFeeDom.innerText = deliverFeeDom.innerText.concat(diner['deliver_fee_'.concat(source)])
    return deliverFeeDom
}

function renderDeliverTime(diner, source){
    let selector = 'deliver_time_'.concat(source)
    let deliverTimeDom = document.getElementById(selector)
    deliverTimeDom.innerText = `${diner['deliver_time_'.concat(source)]}`.concat(deliverTimeDom.innerText)
    return deliverTimeDom
}

function renderColumnName(diner, source){
    let selector = 'column_name_'.concat(source)
    let clolumnNameDom = document.getElementById(selector)
    clolumnNameDom.setAttribute('href', diner['link_'.concat(source)])
    return clolumnNameDom
}

function renderOpenHours(diner, source){
    let openHoursDomSelector = 'open_hours_'.concat(source)
    let openHoursDom = document.getElementById(openHoursDomSelector)
    let openHours = diner['open_hours_'.concat(source)]
    let textArray = ['星期一: ', '星期二: ', '星期三: ', '星期四: ', '星期五: ', '星期六: ', '星期日: ']
    for (let i=0; i < openHours.length; i++){
        for (let r=1; r<8; r++){
            if (openHours[i][0] == r){
                hour = openHours[i]
                textArray[r-1] = textArray[r-1].concat(`${hour[1]} - ${hour[2]}\n`)
        }}
    }
    openHourText = ''
    for (let r=0; r<7; r++){
        if (!(textArray[r].endsWith(': '))){
            openHourText = openHourText.concat(textArray[r])
    }}
    openHoursDom.innerText = openHourText
}

function renderCheaper(diner){
    let cheaperUE = diner['cheaper_ue']
    let cheaperFP = diner['cheaper_fp']
    let cheaperUEDom = document.getElementById('cheaper_ue')
    let cheaperFPDom = document.getElementById('cheaper_fp')
    let text = ''
    for (let i=0; i < cheaperUE.length; i++){
        let key = cheaperUE[i][0]
        let value = cheaperUE[i][1]
        if (value > 0){text = text.concat(`${key}：比熊貓上的同名品項便宜 ${value} 元\n`)}
    }
    cheaperUEDom.innerText = text
    if (text == ''){document.getElementById('cheaper-item_ue').remove()}
    text = ''
    for (let i=0; i < cheaperFP.length; i++){
        let key = cheaperFP[i][0]
        let value = cheaperFP[i][1]
        if (value > 0){text = text.concat(`${key}：比熊貓上的同名品項便宜 ${value} 元\n`)}
    }
    cheaperFPDom.innerText = text
    if (text == ''){document.getElementById('cheaper-item_fp').remove()}
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

function renderMenu(sections, source){
    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);
    let uuidUE = urlParams.get('uuid_ue')
    let uuidFP = urlParams.get('uuid_fp')
    let keys = Object.keys(sections)
    let menuSectionsDom = document.querySelector(`[name=sections_${source}]`)
    let menuPkSectionsDom = document.querySelector(`[name=sections_pk_${source}]`)
    let tabsDom = document.getElementById(`section-tabs_${source}`)
    let tabsPkDom = document.getElementById(`section-tabs_pk_${source}`)
    for (let i=0; i < keys.length; i++){
        let key = keys[i]
        let subsections = sections[key]
        let newSection = dinerSection.cloneNode(true)
        for (let r=0; r < subsections.length; r++){
            let subsection = subsections[r]
            let items = subsection.items
            let newSubsection = dinerSubsection.cloneNode(true)
            let subsctionTitle = subsection.subsection_title
            let subsectionTitleDom = newSubsection.querySelector('[name=subsection-title]')
            subsectionTitleDom.addEventListener('click', function(e){
                toggleItems(e.target)
            })
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
                if (itemImage == ""){imageDom.remove()} else{ imageDom.setAttribute('src', itemImage)}
                descriptionDom.innerText = itemDescription
                $(newItem).show()
                newItemsDom.appendChild(newItem)
            }
            $(newItemsDom).hide()
            newSubsection.appendChild(newItemsDom)
            $(newSubsection).show()
            newSection.appendChild(newSubsection)
        }
        let newTabDom = tabDom.cloneNode(true)
        newTabDom.innerText = key
        newTabDom.setAttribute('data-source', source)
        $(newTabDom).show()
        let newPkTabDom = tabPkDom.cloneNode(true)
        newPkTabDom.innerText = key
        newPkTabDom.setAttribute('data-source', source)
        tabsDom.appendChild(newTabDom)
        let newPkSection = newSection.cloneNode(true)
        newSection.setAttribute('data-section-title', key)
        newSection.setAttribute('data-source', source)
        $(newSection).show()
        menuSectionsDom.appendChild(newSection)
        if (uuidUE && uuidFP){
            $(newPkTabDom).show()
            tabsPkDom.appendChild(newPkTabDom)
            newPkSection.setAttribute('data-section-title-pk', key)
            newPkSection.setAttribute('data-source', source)
            $(newPkSection).hide()
            $(newPkSection).find('[name=subsection-title]').click(function(e){
                toggleItems(e.target)
            })
            menuPkSectionsDom.appendChild(newPkSection)
        }
    }
}

function toggleItems(subsectionTitleDom){
    let itemsDom = subsectionTitleDom.parentNode.nextElementSibling
    $(itemsDom).toggle()
}

function removeUEFPMenu(){
    document.getElementById('menu_ue').remove()
    document.getElementById('menu_fp').remove()
    document.getElementById('divider_ue').remove()
    document.getElementById('divider_fp').remove()
}

const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.addEventListener('mouseenter', Swal.stopTimer)
      toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
  })
  
document.addEventListener('click', (e)=>{
    if (e.target.getAttribute('name') == 'nq-btn'){
        let btn = e.target
        let data = {
            'uuid_ue': btn.getAttribute('data-uuid-ue'),
            'uuid_fp': btn.getAttribute('data-uuid-fp'),
            'uuid_gm': btn.getAttribute('data-uuid-gm')
        }
        showLoading()
        ajaxPost(nqAPI, data, function(response){
            console.log(response)
            endLoading()
            Toast.fire({
                icon: 'success',
                title: '回報成功！'
              })
        })
    }
})


function addUENQFPBtn(uuidUE, uuidFP, uuidGM){
    let btnGroup = document.getElementById('re-btn-group')
    let btn = document.querySelector('[name="re-btn"]').cloneNode(true)
    btn.innerText = 'UE != FP'
    btn.setAttribute('name', 'nq-btn')
    btn.setAttribute('data-uuid-ue', uuidUE)
    btn.setAttribute('data-uuid-fp', uuidFP)
    btn.setAttribute('data-uuid-gm', uuidGM)
    btnGroup.appendChild(btn)
}

function addUENQGMBtn(uuidUE, uuidFP, uuidGM){
    let btnGroup = document.getElementById('re-btn-group')
    let btn = document.querySelector('[name="re-btn"]').cloneNode(true)
    btn.innerText = 'UE != GM'
    btn.setAttribute('name', 'nq-btn')
    btn.setAttribute('data-uuid-ue', uuidUE)
    btn.setAttribute('data-uuid-fp', uuidFP)
    btn.setAttribute('data-uuid-gm', uuidGM)
    btnGroup.appendChild(btn)
}

function addFPNQGMBtn(uuidUE, uuidFP, uuidGM){
    let btnGroup = document.getElementById('re-btn-group')
    let btn = document.querySelector('[name="re-btn"]').cloneNode(true)
    btn.innerText = 'FP != GM'
    btn.setAttribute('name', 'nq-btn')
    btn.setAttribute('data-uuid-ue', uuidUE)
    btn.setAttribute('data-uuid-fp', uuidFP)
    btn.setAttribute('data-uuid-gm', uuidGM)
    btnGroup.appendChild(btn)
}

showLoading()
ajaxGet(dinerInfoAPI, function(response){
    console.log(response)
    let uuidGM = response.data.uuid_gm
    if (uuidUE){
        renderDiner(response, 'ue')
        $('#info_ue').show()
    } else {
        removeDiner('ue')
    }
    if (uuidFP){
        renderDiner(response, 'fp')
        $('#info_fp').show()
    }
    else {
        removeDiner('fp')
    }
    if (!(uuidUE) | !(uuidFP)){
        removePk()
    }
    if (uuidUE && uuidFP){
        renderCheaper(response.data)
        removeUEFPMenu()
    }
    if (uuidUE && uuidFP && uuidGM){
        addUENQFPBtn(uuidUE, uuidFP, uuidGM)
        addUENQGMBtn(uuidUE, uuidFP, uuidGM)
        addFPNQGMBtn(uuidUE, uuidFP, uuidGM)
    } else if (uuidUE && uuidGM){
        addUENQGMBtn(uuidUE, uuidFP, uuidGM)
        renderGMInfo(response)
    } else if (uuidFP && uuidGM){
        addFPNQGMBtn(uuidUE, uuidFP, uuidGM)
        renderGMInfo(response)
    } else if (uuidUE && uuidFP){
        renderCheaper(response.data)
        removeUEFPMenu()
        addUENQFPBtn(uuidUE, uuidFP, uuidGM)
    } else {
        removeGM()
    }
    $('#diner-info').show()
    $('[data-section-title]').hide()
    endLoading()
})

document.addEventListener('click', (e)=>{
    if (e.target.getAttribute('id') == 'show-more-info_ue'){
        let openHoursDomUe = document.getElementById('open_hours_ue').cloneNode(true) 
        Swal.fire(
            {
            title: '服務時間',
            html: openHoursDomUe,
            customClass: 'justify-content-center'
        })
    } else if (e.target.getAttribute('id') == 'show-more-info_fp'){
        let openHoursDomFp = document.getElementById('open_hours_fp').cloneNode(true)
        Swal.fire({
            title: '服務時間',
            html: openHoursDomFp,
            customClass: 'justify-content-center'
        })
    }
})

document.addEventListener('click', (e)=>{
    if (e.target.getAttribute('id') == 'cheaper-item_ue'){
        let cheaperDomUE = document.getElementById('cheaper_ue').cloneNode(true) 
        Swal.fire(
            {
            title: 'Uber Eats 優勢品項',
            html: cheaperDomUE,
            customClass: 'justify-content-center'
        })
    } else if (e.target.getAttribute('id') == 'cheaper-item_fp'){
        let cheaperDomFP = document.getElementById('cheaper_fp').cloneNode(true)
        Swal.fire({
            title: 'Food Panda 優勢品項',
            html: cheaperDomFP,
            customClass: 'justify-content-center'
        })
    }
})

document.addEventListener('click', (e)=>{
    if (e.target.getAttribute('name') == 'section-tab'){
        let dataSectionTitle = e.target.innerText
        let source = e.target.getAttribute('data-source')
        $(`[name=section][data-source=${source}][data-section-title][data-section-title!="${dataSectionTitle}"]`).hide()
        $(`[name=section-tab][data-source=${source}]:contains('${dataSectionTitle}')`).toggleClass('clicked')
        $(`[name=section-tab][data-source=${source}]:not(:contains('${dataSectionTitle}'))`).toggleClass('clicked')
        $(`[data-section-title="${dataSectionTitle}"][data-source=${source}]`).toggle()
    } else if (e.target.getAttribute('name') == 'section-tab-pk'){
        let dataSectionTitle = e.target.innerText
        let source = e.target.getAttribute('data-source')
        $(`[name=section-tab-pk][data-section-title][data-source=${source}][data-section-title!="${dataSectionTitle}"]`).hide()
        $(`[name=section-tab-pk][data-source=${source}]:contains('${dataSectionTitle}')`).toggleClass('clicked')
        $(`[name=section-tab-pk][data-source=${source}]:not(:contains('${dataSectionTitle}'))`).toggleClass('clicked')
        $(`[data-section-title-pk="${dataSectionTitle}"][data-source=${source}]`).toggle()
    }
})
