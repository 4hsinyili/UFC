let today = new Date();
let dd = String(today.getDate()).padStart(2, '0');
let mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
let yyyy = today.getFullYear();
let startDateDom = document.querySelector('#start-date')
let endDateDom = document.querySelector('#end-date')
let dateFormvalue = `${yyyy}-${mm}-${dd}`
startDateDom.value = dateFormvalue
endDateDom.value = dateFormvalue

let statesGraph = document.getElementById('states-graph');
let lambdaGraph = document.getElementById('lambda-graph');
let matchGraph = document.getElementById('match-graph');
let placeGraph = document.getElementById('place-graph');
let dashboardApi = 'api/v1/dashboard'

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

// function render(data){
//     if(data.data == null){
//         allUserCountShow.textContent = `All user count: 0`;
//         let act_source = [{
//             type: 'funnel',
//             x: [0,0,0,0],
//             y: ["View", "View Item", "Add to Cart", "Checkout"]
//         }]
//         Plotly.newPlot( FUNNEL, act_source, {
//         margin: { t: 0 } } );
        
//         let user_source = [{
//             type: 'bar',
//             x: ['active_user', 'new_user', 'return_user'],
//             y: [0,0,0]
//         }]
//         Plotly.newPlot( BAR, user_source, {
//         margin: { t: 0 } } );
//     } else{
//         allUserCountShow.textContent = `All user count: ${data.data.all_user_count}`;
//         let act_source = [{
//             type: 'funnel',
//             x: [data.data.view_count, data.data.view_item_count, data.data.add_to_cart_count, data.data.checkout_count],
//             y: ["View", "View Item", "Add to Cart", "Checkout"]
//         }]
//         Plotly.newPlot( FUNNEL, act_source, {
//         margin: { t: 0 } } );
        
//         let user_source = [{
//             type: 'bar',
//             x: ['active_user', 'new_user', 'return_user'],
//             y: [data.data.active_user_count, data.data.new_user_count, data.data.returned_user_count]
//         }]
//         Plotly.newPlot( BAR, user_source, {
//         margin: { t: 0 } } );
//     }
//    }

document.getElementById('select-dates').addEventListener('change', (e)=>{
    let startDate = startDateDom.value
    let endDate = endDateDom.value
    let data = {'start_date': startDate, 'end_date': endDate}
    ajaxPost(dashboardApi, data, function(response){
        console.log(response)
    })
})

// ajax(getUrl, function(response){
//     render(response); });

// setInterval(function(){ajax(`api/1.0/dashboard?scope=${scopeForm.value}&date=${dateForm.value}`, function(response){
//     render(response)
// })}, 5000);