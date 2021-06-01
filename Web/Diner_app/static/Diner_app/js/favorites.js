// API related variables
let userId = parseInt(document.getElementById('user-id').getAttribute('data-user-id'))
let dinerSearchAPI = 'api/v1/dinersearch'
let dinerShuffleAPI = 'api/v1/dinershuffle'
let favoritesAPI = 'api/v1/favorites'
let getFavoritesAPI = favoritesAPI.concat('?user_id=').concat(userId)
let domain = window.location.origin
let dinerInfoRoute = domain.concat('/dinerinfo')
let initData = {'condition': {}, 'offset': 0, 'user_id': userId}
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
let dinerTemplate = document.getElementById('diner-template')
let dinersHtml = diners.innerHTML

let ratingSvg = document.querySelector('[name="rating_svg"]')
let viewCountSvg = document.querySelector('[name="view_count_svg"]')
let budgetSvg = document.querySelector('[name=budget_svg]')

let showMoreDom = $('div[id="show-more"]')[0]

let collectDom = $('[name="collect"]')[0]

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
    let collectNode = dinerNode.querySelector('[name=collect]')
    let diner_uuid_ue = diner['uuid_ue']
    let diner_uuid_fp = diner['uuid_fp']
    dinerNode.setAttribute('data-uuid_ue', diner_uuid_ue)
    dinerNode.setAttribute('data-uuid_fp', diner_uuid_fp)
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
        if (userId > 0){collectNode.setAttribute('data-uuid-ue', diner_uuid_ue)}
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
        if (userId > 0){collectNode.setAttribute('data-uuid-fp', diner_uuid_fp)}
    }
    if (diner_info_ue){ renderDinerInfo(diner_info_ue, dinerNode, 'ue')}
    if (diner_info_fp){ renderDinerInfo(diner_info_fp, dinerNode, 'fp')}
    if (diner['favorite']){collectNode.setAttribute('data-favorite', 1)}
    else {collectNode.setAttribute('data-favorite', 0)}
    collectNode.addEventListener('click', (e)=>{
        if (userId == 0){alert('login la')}
        else{
            let favorited = parseInt(e.target.getAttribute('data-favorite'))
            let activate = 0
            if (favorited == 0){activate = 1}
            let uuid_ue = e.target.getAttribute('data-uuid-ue')
            let uuid_fp = e.target.getAttribute('data-uuid-fp')
            if (uuid_ue){changeFavorites(userId, uuid_ue, 'ue', activate)}
            if (uuid_fp){changeFavorites(userId, uuid_fp, 'fp', activate)}
            if (activate == 1){e.target.setAttribute('data-favorite', 1)}
            if (activate == 0){
                e.target.setAttribute('data-favorite', 0)
                if(uuid_ue)(document.querySelector(`[data-uuid_ue="${uuid_ue}"]`).remove())
                else if(uuid_fp)(document.querySelector(`[data-uuid_fp="${uuid_fp}"]`).remove())
            }
        }
    })
    return dinerNode
}

function renderList(data){
    let results = data.data
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


function changeFavorites(userId, diner_id, source, activate){
    let data = {
        'user_id': userId,
        'source': source,
        'activate': activate
    }
    if (source == 'ue'){data.uuid_ue = diner_id}
    else if(source == 'fp'){data.uuid_fp = diner_id}
    ajaxPost(favoritesAPI, data, console.log)
}

// start to render
ajaxGet(getFavoritesAPI.concat('&offset=0'), function(response){
    if (response.is_data == true){renderList(response)}
})


$(showMoreDom).click(function(){
    $(showMoreDom).hide()
    let offset = parseInt(showMoreDom.getAttribute('data-offset'))
    ajaxGet(getFavoritesAPI.concat(`&offset=${offset}`), function(response){
        if (response.is_data == true){renderList(response)}
    })
})

