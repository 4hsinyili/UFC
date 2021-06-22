const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const uuidUE = urlParams.get('uuid_ue')
const uuidFP = urlParams.get('uuid_fp')
const dinerInfoAPI = 'api/v1/dinerinfo'.concat('?uuid_ue=').concat(uuidUE).concat('&uuid_fp=').concat(uuidFP)
const nqAPI = 'api/v1/noteq'
const favoritesAPI = 'api/v1/favorites'

const dinerSection = document.querySelector('[name=section]')
const dinerSubsection = document.querySelector('[name=subsection]')
const dinerItems = document.querySelector('[name=items]')
const dinerItem = document.querySelector('[name=item]')
const tabDom = document.querySelector('[name=section-tab]')
const tabPkDom = document.querySelector('[name=section-tab-pk]')

const reportError = document.getElementById('report-error')
const updateFavorite = document.getElementById('update-favorite')
const csrftoken = getCookie('csrftoken');

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

$('#diner-info').hide()


function renderDiner(response, source){
    let dinerInfo = response.data
    let sections = pivotMenu(dinerInfo, source)

    renderTitle(dinerInfo, source)
    renderImage(dinerInfo, source)
    renderRating(dinerInfo, source)
    renderViewCount(dinerInfo, source)
    renderDeliverFee(dinerInfo, source)
    renderDeliverTime(dinerInfo,source)
    renderOpenHours(dinerInfo, source)
    renderMenu(sections, source)
    renderColumnName(dinerInfo, source)
    renderFavorites(dinerInfo)
    renderTags(dinerInfo, source)
}

function renderFavorites(dinerInfo){
    updateFavorite.setAttribute('data-uuid_ue', dinerInfo.uuid_ue)
    updateFavorite.setAttribute('data-uuid_fp', dinerInfo.uuid_fp)
    if (dinerInfo.favorite){
        updateFavorite.innerText = '已收藏'
        updateFavorite.setAttribute('data-activate', 1)
        updateFavorite.style.color = '#D18384'
    } else {
        updateFavorite.innerText = '未收藏'
        updateFavorite.setAttribute('data-activate', 0)   
        updateFavorite.style.color = '#0d6efd'
    }
    favoriteListener(updateFavorite)
}

function toggleFavorite(favBtn){
    let data = {
        'uuid_ue': $(favBtn).attr('data-uuid_ue'),
        'uuid_fp': $(favBtn).attr('data-uuid_fp'),
    }
    if ($(favBtn).attr('data-activate') == 0){
        favBtn.innerText = '已收藏'
        favBtn.setAttribute('data-activate', 1)
        favBtn.style.color = '#D18384'
        data.activate = 1
    } else {
        updateFavorite.innerText = '未收藏'
        updateFavorite.setAttribute('data-activate', 0)   
        updateFavorite.style.color = '#0d6efd'
        data.activate = 0
    }
    ajaxPost(favoritesAPI, data, doNothing)
}

function hoverFavorite(favBtn){
    if ($(favBtn).attr('data-activate') == 0){
        favBtn.innerText = '加入收藏'
    } else {
        updateFavorite.innerText = '移除收藏'
    }
}

function outFavorite(favBtn){
    if ($(favBtn).attr('data-activate') == 0){
        favBtn.innerText = '未收藏'
    } else {
        updateFavorite.innerText = '已收藏'
    }
}

function favoriteListener(favBtn){
    favBtn.addEventListener('click', (e)=>{
        toggleFavorite(e.target)
    })
    favBtn.addEventListener('mouseover', (e)=>{
        hoverFavorite(e.target)
    })
    favBtn.addEventListener('mouseleave', (e)=>{
        outFavorite(e.target)
    })
}

function renderGMInfo(response){
    let dinerInfo = response.data
    renderRating(dinerInfo, 'gm')
    renderViewCount(dinerInfo, 'gm')
    renderColumnName(dinerInfo, 'gm')
}

function removeGM(){
    document.getElementById(`column_name_gm`).remove()
    document.getElementById(`rating_gm`).remove()
    document.getElementById(`view_count_gm`).remove()
    document.getElementById('deliver_fee_gm').remove()
    document.getElementById('show-more-info_gm').remove()
    document.getElementById('deliver_time_gm').remove()
}

function removeDiner(source){
    document.getElementById(`title_${source}`).remove()
    document.getElementById(`rating_${source}`).remove()
    document.getElementById(`image_${source}`).remove()
    document.getElementById(`view_count_${source}`).remove()
    document.getElementById(`deliver_fee_${source}`).remove()
    document.getElementById(`deliver_time_${source}`).remove()
    document.getElementById(`open_hours_${source}`).remove()
    document.getElementById(`menu-col_${source}`).remove()
    if (source == 'ue') {document.getElementById('menu-col_fp').className = 'col'}
    if (source == 'fp') {document.getElementById('menu-col_ue').className = 'col'}
    document.getElementById(`column_name_${source}`).remove()
    document.getElementById(`show-more-info_${source}`).remove()
    document.getElementById(`detail_${source}`).remove()
    document.getElementById(`tags_${source}`).remove()
}

function renderTitle(dinerInfo, source){
    let selector = 'title_'.concat(source)
    let titleDom = document.getElementById(selector)
    titleDom.innerText = dinerInfo['title_'.concat(source)]
    titleDom.setAttribute('href', dinerInfo['link_'.concat(source)])
    let webTitle = document.getElementById('web-title')
    webTitle.innerText = webTitle.innerText.concat(' | ').concat(dinerInfo['title_'.concat(source)])
    return titleDom
}

function renderImage(dinerInfo, source){
    let selector = 'image_'.concat(source)
    let imageDom = document.getElementById(selector)
    imageDom.setAttribute('src', dinerInfo['image_'.concat(source)])
    return imageDom
}

function renderRating(dinerInfo, source){
    let selector = 'rating_'.concat(source)
    let ratingDom = document.getElementById(selector)
    ratingDom.innerText = ratingDom.innerText.concat(dinerInfo['rating_'.concat(source)])
    return ratingDom
}

function renderViewCount(dinerInfo, source){
    let selector = 'view_count_'.concat(source)
    let viewCountDom = document.getElementById(selector)
    viewCountDom.innerText = viewCountDom.innerText.concat(dinerInfo['view_count_'.concat(source)])
    return viewCountDom
}

function renderBudget(dinerInfo, source){
    let selector = 'budget_'.concat(source)
    let budgetDom = document.getElementById(selector)
    budgetDom.innerText = budgetDom.innerText.concat('$'.repeat(dinerInfo['budget_'.concat(source)]))
    return budgetDom
}

function renderDeliverFee(dinerInfo, source){
    let selector = 'deliver_fee_'.concat(source)
    let deliverFeeDom = document.getElementById(selector)
    deliverFeeDom.innerText = deliverFeeDom.innerText.concat(dinerInfo['deliver_fee_'.concat(source)])
    return deliverFeeDom
}

function renderDeliverTime(dinerInfo, source){
    let selector = 'deliver_time_'.concat(source)
    let deliverTimeDom = document.getElementById(selector)
    deliverTimeDom.innerText = `${dinerInfo['deliver_time_'.concat(source)]}`.concat(deliverTimeDom.innerText)
    return deliverTimeDom
}

function renderColumnName(dinerInfo, source){
    let selector = 'column_name_'.concat(source)
    let clolumnNameDom = document.getElementById(selector)
    clolumnNameDom.setAttribute('href', dinerInfo['link_'.concat(source)])
    return clolumnNameDom
}

function renderOpenHours(dinerInfo, source){
    let openHoursDomSelector = 'open_hours_'.concat(source)
    let openHoursDom = document.getElementById(openHoursDomSelector)
    let openHours = dinerInfo['open_hours_'.concat(source)]
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

function renderTags(dinerInfo, source){
    let selector = 'tags_'.concat(source)
    let tagsDom = document.getElementById(selector)
    let tags = dinerInfo['tags_'.concat(source)]
    let tagsText = tagsDom.innerText
    for (let tag of tags){
        tagsText = tagsText.concat('#').concat(tag).concat(' ')
    }
    tagsDom.innerText = tagsText
    return tagsDom
}

function renderCheaper(dinerInfo){
    let cheaperUE = dinerInfo['cheaper_ue']
    let cheaperFP = dinerInfo['cheaper_fp']
    let cheaperUEDom = document.getElementById('cheaper_ue')
    let cheaperFPDom = document.getElementById('cheaper_fp')
    let text = ''
    for (let i=0; i < cheaperUE.length; i++){
        let key = cheaperUE[i][0]
        let value = cheaperUE[i][1]
        if (value > 0){text = text.concat(`${key}：比 Food Panda 上的同名品項便宜 ${value} 元\n`)}
    }
    cheaperUEDom.innerText = text
    if (text == ''){document.getElementById('cheaper-item_ue').remove()}
    text = ''
    for (let i=0; i < cheaperFP.length; i++){
        let key = cheaperFP[i][0]
        let value = cheaperFP[i][1]
        if (value > 0){text = text.concat(`${key}：比 Uber Eats 上的同名品項便宜 ${value} 元\n`)}
    }
    cheaperFPDom.innerText = text
    if (text == ''){document.getElementById('cheaper-item_fp').remove()}
}

function removeCheaper(source){
    document.getElementById('cheaper-item_'.concat(source)).remove()
}

function pivotMenu(dinerInfo,source){
    let menus = dinerInfo['menu_'.concat(source)]
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
        let subCateTitle = menu.subsection_title
        subsectionTitleSet.push(subCateTitle)
        let items = {
            'subsection_title': subCateTitle,
            'items': menu.items
        }
        sections[sectionTitle].push(items)
    }
    return sections
}

function renderMainCate(mainCateSel, subCateSelS, sections, key, index, source){
    let newOpt = document.createElement('option')
    newOpt.value = index
    newOpt.innerText = key
    mainCateSel.appendChild(newOpt)
    
    let newSubCateSel = document.getElementsByName('sub-cate')[0].cloneNode(true)
    newSubCateSel.name = 'sub-cate_'.concat(source)
    $(newSubCateSel).attr('data-main-cate-number', index)
    $(newSubCateSel).attr('data-source', source)
    subCateSelS.appendChild(newSubCateSel)

    let subCates = sections[key]
    let newMainCate = dinerSection.cloneNode(true)

    newSubCateSel.addEventListener('change', (e)=>{
        toggleSubCate(e.target)
    })

    return {
        "mainCateSel": mainCateSel,
        "subCates": subCates,
        "newMainCate": newMainCate,
        "newSubCateSel": newSubCateSel
    }
}

function renderSubCate(subCate, newSubCateSel, index, source){
    let newSubCateDom = dinerSubsection.cloneNode(true)

    newSubCateDom.setAttribute('data-source', source)

    let items = subCate.items
    let subCateTitle = subCate.subsection_title
    
    let newSubOpt = document.createElement('option')

    newSubOpt.value = index
    newSubOpt.innerText = subCateTitle
    newSubCateSel.appendChild(newSubOpt)
    
    let newItemsDom = dinerItems.cloneNode(true)
    $(newSubCateDom).attr('data-sub-cate-number', index)

    return {
        'newSubCateDom': newSubCateDom,
        'items': items,
        'newItemsDom': newItemsDom
    }
}

function renderItem(item, newItemsDom){
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

function renderMenu(sections, source){
    let keys = Object.keys(sections)
    let mainCateSel = document.getElementById('main-cate_'.concat(source))
    let subCateSelS = document.getElementById('sub-cates_'.concat(source))
    
    mainCateSel.setAttribute('data-source', source)
    mainCateSel.addEventListener('change', (e)=>{
        toggleSubCateSel(e.target)
    })

    for (let i=0; i < keys.length; i++){
        let key = keys[i]
        let mainCateObject = renderMainCate(
            mainCateSel,
            subCateSelS,
            sections,
            key,
            i,
            source)
        
        let subCates = mainCateObject.subCates
        let newSubCateSel = mainCateObject.newSubCateSel
        let newMainCate = mainCateObject.newMainCate

        for (let r=0; r < subCates.length; r++){
            let subCateObject = renderSubCate(
                subCates[r],
                newSubCateSel,
                r,
                source)
            
            let items = subCateObject.items
            let newItemsDom = subCateObject.newItemsDom
            let newSubCateDom = subCateObject.newSubCateDom

            for (let item of items){
                renderItem(item, newItemsDom)
            }
            $(newItemsDom).show()
            newSubCateDom.appendChild(newItemsDom)
            newMainCate.appendChild(newSubCateDom)
            document.getElementById('sub-cate_'.concat(source)).appendChild(newSubCateDom)
        }
    }
}

function toggleSubCateSel(target){
    let dataMainCateNum = target.value
    let source = target.getAttribute('data-source')
    let subCates = document.querySelectorAll(`[name="sub-cate_${source}"]`)
    let chosedSubCates = document.querySelector(`[name="sub-cate_${source}"][data-main-cate-number="${dataMainCateNum}"]`)
    $(subCates).hide()
    $(chosedSubCates).show()
    return chosedSubCates
}

function toggleSubCate(target){
    let dataSubCateNum = target.value
    let source = target.getAttribute('data-source')
    let subCates = document.querySelectorAll(`[name="subsection"][data-source=${source}]`)
    let chosedSubCates = document.querySelector(`[name="subsection"][data-source=${source}][data-sub-cate-number="${dataSubCateNum}"]`)
    $(subCates).hide()
    $(chosedSubCates).show()
}

function removeUEFPMenu(){
    document.getElementById('menu_ue').remove()
    document.getElementById('menu_fp').remove()
    document.getElementById('divider_ue').remove()
    document.getElementById('divider_fp').remove()
}

function addNEBtn(uuidUE, uuidFP, uuidGM, innerText){
    let btnGroup = document.getElementById('re-btn-group')
    let btn = document.querySelector('[name="re-btn"]').cloneNode(true)
    btn.innerText = innerText
    $(btn).addClass('btn-primary')
    btn.setAttribute('name', 'nq-btn')
    btn.setAttribute('data-uuid-ue', uuidUE)
    btn.setAttribute('data-uuid-fp', uuidFP)
    btn.setAttribute('data-uuid-gm', uuidGM)
    btnGroup.appendChild(btn)
}

showLoading()
ajaxGet(dinerInfoAPI, function(response){
    let uuidUE = response.data.uuid_ue
    let uuidFP = response.data.uuid_fp
    let uuidGM = response.data.uuid_gm
    if (uuidUE && uuidFP && uuidGM){
        renderDiner(response, 'ue')
        renderDiner(response, 'fp')
        $('#info_ue').show()
        $('#info_fp').show()

        addNEBtn(uuidUE, uuidFP, uuidGM, 'UE != FP')
        addNEBtn(uuidUE, uuidFP, uuidGM, 'UE != GM')
        addNEBtn(uuidUE, uuidFP, uuidGM, 'FP != GM')
        renderCheaper(response.data)

    } else if (uuidUE && uuidGM){

        renderDiner(response, 'ue')
        addNEBtn(uuidUE, uuidFP, uuidGM, 'UE != GM')
        removeDiner('fp')
        renderGMInfo(response)
        removeCheaper('ue')

    } else if (uuidFP && uuidGM){

        renderDiner(response, 'fp')
        addNEBtn(uuidUE, uuidFP, uuidGM, 'FP != GM')
        removeDiner('ue')
        renderGMInfo(response)
        removeCheaper('fp')

    } else if (uuidUE && uuidFP){

        renderDiner(response, 'ue')
        renderDiner(response, 'fp')
        addNEBtn(uuidUE, uuidFP, uuidGM, 'UE != FP')
        renderCheaper(response.data)

    } else if (uuidUE){

        renderDiner(response, 'ue')
        removeDiner('fp')
        removeGM()
        removeCheaper('ue')

    } else if (uuidFP){

        renderDiner(response, 'fp')
        removeDiner('ue')
        removeGM()
        removeCheaper('fp')

    }
    $('#diner-info').show()
    $('[data-section-title]').hide()
    
    if (uuidUE){
        let mainSelUE = document.getElementById('main-cate_ue')
        let chosedSubCates = toggleSubCateSel(mainSelUE)
        toggleSubCate(chosedSubCates)
        
    }
    if (uuidFP){
        let mainSelFP = document.getElementById('main-cate_fp')
        let chosedSubCates = toggleSubCateSel(mainSelFP)
        toggleSubCate(chosedSubCates)
        
    }
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
    if (e.target.getAttribute('name') == 'nq-btn'){
        let btn = e.target
        let data = {
            'uuid_ue': btn.getAttribute('data-uuid-ue'),
            'uuid_fp': btn.getAttribute('data-uuid-fp'),
            'uuid_gm': btn.getAttribute('data-uuid-gm')
        }
        showLoading()
        ajaxPost(nqAPI, data, function(response){
            endLoading()
            Toast.fire({
                icon: 'success',
                title: '回報成功！'
              })
        })
    }
})

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
            customClass: 'justify-content-center',
            showConfirmButton: false
        })
    }
})