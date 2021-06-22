// API related variables
const dinerSearchAPI = 'api/v1/dinersearch'
const dinerShuffleAPI = 'api/v1/dinershuffle'
const favoritesAPI = 'api/v1/favorites'
const getFavoritesAPI = favoritesAPI
const domain = window.location.origin
const dinerInfoRoute = domain.concat('/dinerinfo')

const initData = {'condition': {}, 'offset': 0}
// Doms
const diners = document.getElementById('diners')
const dinerTemplate = document.getElementById('diner-template')
const dinersHtml = diners.innerHTML

const showMoreDom = document.querySelector('div[id="show-more"]')

const divederRow = document.querySelector('[name="divider-row"]')

// Define functions
const csrftoken = getCookie('csrftoken');


// start to render
showLoading()
ajaxGet(getFavoritesAPI.concat('?offset=0'), function(response){
    if (response.no_data == false){
        renderList(response)
        endLoading()
    }
    else {
        endLoading()
        let hintDom = document.getElementById('no-diners').cloneNode(true)
        $(hintDom).show()
        Swal.fire(
            {
            title: '目前還沒有收藏喔！',
            html: hintDom,
            showConfirmButton: false
        })
    }
})


$(showMoreDom).click(function(){
    let offset = parseInt(showMoreDom.getAttribute('data-offset'))
    let height = $(document).height()
    $(showMoreDom).hide()
    showLoading()
    ajaxGet(getFavoritesAPI.concat(`?offset=${offset}`), function(response){
        if (response.no_data == false){renderList(response)}
        window.scrollTo(0,(height - (200)));
        endLoading()
    })
})


