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
    } else if (initaialXhr.status == 403){
        forbidden()
    }
    };
} 

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

function forbidden(){
    Swal.fire({
        title: "請求遭拒",
        text: "嗨，你可能在短時間內刷新了太多次頁面，或是瀏覽器的快取出了點問題，請嘗試清除快取（ctrl+shift+del）再重新整理。",
        footer: '如果持續看到這段訊息，請聯絡開發者：4hsinyili@gmail.com'
    });
}

function showLoading(){
    Swal.fire({
        title: "",
        text: "Loading...",
        didOpen: ()=>{
            Swal.showLoading()
        }
    });
}

function endLoading() {
    Swal.close()
}

$(window).bind('beforeunload', function(){
    let lastVisitUrl = window.location.href
    if (lastVisitUrl.endsWith('login')){}
    else if (lastVisitUrl.endsWith('register')){}
    else (Cookies.set('ufc_last_visit', lastVisitUrl))
});