function renderDinerInfo(dinerInfo, redirectUrl, dinerDom, source){
    renderTitle(dinerInfo, dinerDom, source)
    renderImage(dinerInfo, dinerDom, source)
    renderRatingViewCount(dinerInfo, dinerDom, source)
    renderLink(dinerInfo, dinerDom, source)
    renderTags(dinerInfo, dinerDom, source)
    renderDeliverFeeTime(dinerInfo, dinerDom, source)
    renderRedirectUrl(redirectUrl, dinerDom, source)
}

function renderTitle(dinerInfo, dinerDom, source){
    let title = dinerInfo['title_'.concat(source)]
    let titleNode = dinerDom.querySelector('.title_'.concat(source))
    titleNode.innerText = title
}

function renderImage(dinerInfo, dinerDom, source){
    let image = dinerInfo['image_'.concat(source)]
    let imageNode = dinerDom.querySelector('.image_'.concat(source))
    imageNode.setAttribute('src', image)
}

function renderRatingViewCount(dinerInfo, dinerDom, source){
    let rating = dinerInfo['rating_'.concat(source)]
    let viewCount = dinerInfo['view_count_'.concat(source)]
    if (rating == 0){
        dinerDom.querySelector('.rating_value_'.concat(source)).innerText = '新上架'
    } else {
        dinerDom.querySelector('.rating_value_'.concat(source)).innerText = `${rating}(${viewCount})`
    }
}

function renderLink(dinerInfo, dinerDom, source){
    let link = dinerInfo['link_'.concat(source)]
    dinerDom.querySelector('#link_'.concat(source)).setAttribute('href', link)
}

function renderTags(dinerInfo, dinerDom, source){
    let tags = dinerInfo['tags_'.concat(source)]
    let tagsText = dinerDom.querySelector('.tags_'.concat(source)).innerText
    for (let tag of tags){
        tagsText = tagsText.concat('#').concat(tag).concat(' ')
    }
    dinerDom.querySelector('.tags_'.concat(source)).innerText = tagsText
}

function renderDeliverFeeTime(dinerInfo, dinerDom, source){
    let deliver_fee = dinerInfo['deliver_fee_'.concat(source)]
    let deliver_time = dinerInfo['deliver_time_'.concat(source)]
    if ((deliver_fee == 0) && (deliver_time == 0)){
        dinerDom.querySelector('.deliver_fee_time_'.concat(source)).innerText = `NaN`
    } else if (deliver_fee == 0){
        dinerDom.querySelector('.deliver_fee_time_'.concat(source)).innerText = `NaN(${deliver_time} 分鐘)`
    } else if (deliver_time == 0){
        dinerDom.querySelector('.deliver_fee_time_'.concat(source)).innerText = `$${deliver_fee}(NaN)`
    } else {
        dinerDom.querySelector('.deliver_fee_time_'.concat(source)).innerText = `$${deliver_fee}(${deliver_time})`
    } 
}

function renderRedirectUrl(redirectUrl, dinerDom, source){
    let redirectHrefNodes = dinerDom.querySelectorAll('.redirect-href_'.concat(source))
    for (let redirectHrefNode of redirectHrefNodes){
        redirectHrefNode.setAttribute('href', redirectUrl)
    }
}

function renderFavorite(dinerInfo, dinerDom){
    let favoriteDom = dinerDom.querySelector('[name=favorite].icon')
    favoriteDom.setAttribute('data-favorite', 0)
    favoriteDom.setAttribute('data-uuid-ue', dinerInfo.uuid_ue)
    favoriteDom.setAttribute('data-uuid-fp', dinerInfo.uuid_fp)
    let diner_favorite = dinerInfo['favorite']
    if (diner_favorite){ 
        favoriteDom.setAttribute('data-favorite', 1)
        favoriteDom.setAttribute('src', "https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/heart_filled.svg")
    }
    favoriteDom.addEventListener('click', (e)=>{
        favoriteListener(e.target)
    })
}

function removeInfo(dinerDom, source){
    if ((source == 'ue') || (source == 'fp')){
        let titleDoms = dinerDom.querySelectorAll('.redirect-href_'.concat(source))
        let imageDoms = dinerDom.querySelectorAll('.image_'.concat(source))
        for (let titleDom of titleDoms){
            titleDom.remove()
        }
        for (let imageDom of imageDoms){
            imageDom.remove()
        }
    }
    let infoRow = dinerDom.querySelector('.info_'.concat(source))
    infoRow.remove()
}

function renderGM(dinerInfo, dinerDom, source){
    let rating = dinerInfo['rating_'.concat(source)]
    let viewCount = dinerInfo['view_count_'.concat(source)]
    let link = dinerInfo['link_'.concat(source)]
    dinerDom.querySelector('.rating_value_'.concat(source)).innerText = `${rating}(${viewCount})`
    dinerDom.querySelector('#link_'.concat(source)).setAttribute('href', link)
}

function removeFpTitleImageIfBothExist(dinerDom){
    let titleFp = dinerDom.querySelector('.title_fp')
    let imageNodeFp = dinerDom.querySelector('.image_fp')
    imageNodeFp.remove()
    titleFp.remove()
}

function renderDiner(dinerInfo){
    let dinerDom = dinerTemplate.cloneNode(true)
    let diner_uuid_ue = dinerInfo['uuid_ue']
    let diner_uuid_fp = dinerInfo['uuid_fp']
    let diner_uuid_gm = dinerInfo['uuid_gm']
    let redirectUrl = dinerInfoRoute.concat('?uuid_ue=').concat(diner_uuid_ue).concat('&uuid_fp=').concat(diner_uuid_fp)
    
    if (diner_uuid_ue){
        renderDinerInfo(dinerInfo, redirectUrl, dinerDom, 'ue')
    } else{
        removeInfo(dinerDom, 'ue')
    }
    
    if (diner_uuid_fp){
        renderDinerInfo(dinerInfo, redirectUrl, dinerDom, 'fp')
    } else{
        removeInfo(dinerDom, 'fp')
    }
    
    if (diner_uuid_gm){
        renderGM(dinerInfo, dinerDom, 'gm')
    } else{
        removeInfo(dinerDom, 'gm')
    }

    if (diner_uuid_ue && diner_uuid_fp){
        removeFpTitleImageIfBothExist(dinerDom)
    }
    
    renderFavorite(dinerInfo, dinerDom)
    return dinerDom
}

function favoriteListener(favoriteDom){
    let favorited = parseInt(favoriteDom.getAttribute('data-favorite'))
    let activate = 0
    let uuid_ue = favoriteDom.getAttribute('data-uuid-ue')
    let uuid_fp = favoriteDom.getAttribute('data-uuid-fp')
    
    if (favorited == 0){activate = 1}

    changeFavorites(uuid_ue, uuid_fp, activate)
    
    if (activate == 1){
        favoriteDom.setAttribute('data-favorite', 1)
        favoriteDom.setAttribute('src', "https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/heart_filled.svg")
    } else if (activate == 0){
        favoriteDom.setAttribute('data-favorite', 0)
        favoriteDom.setAttribute('src', "https://appworks-school-hsinyili.s3-ap-northeast-1.amazonaws.com/heart.svg")
    }
}

function renderList(data){
    if (data.no_data == 1){
        return false
    }
    let dinersInfo = data.data
    for (let dinerInfo of dinersInfo){
        let newDividerRow = divederRow.cloneNode(true)
        diner = renderDiner(dinerInfo)
        diners.appendChild(diner)
        diners.appendChild(newDividerRow)
        $(newDividerRow).show()
        $(diner).show()
    }
    if (data.has_more == true){
        showMoreDom.setAttribute('data-offset', data.next_offset)
        $(showMoreDom).show()
    } else {
        $(showMoreDom).hide()
    }
    return true
}

function renderMore(data){
    renderList(data)
    window.scrollTo(0,(document.body.scrollHeight - window.innerHeight));
}

function doNothing(){}

function changeFavorites(uuid_ue, uuid_fp, activate){
    let data = {
        'uuid_ue': uuid_ue,
        'uuid_fp': uuid_fp,
        'activate': activate
    }
    ajaxPost(favoritesAPI, data, doNothing)
}