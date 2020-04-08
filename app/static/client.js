var el = x => document.getElementById(x);

function answer() {
    var article_text = el('article-text').value;
    var question_text = el('question-text').value;

    el('answer-button').innerHTML = 'Answering...';
    var xhr = new XMLHttpRequest();
    var loc = window.location
    xhr.open('POST', `${loc.protocol}//${loc.hostname}:${loc.port}/answer`, true);
    xhr.onerror = function() {alert (xhr.responseText);}
    xhr.onload = function(e) {
        if (this.readyState === 4) {
            var response = JSON.parse(e.target.responseText);
            el('answer-label').innerHTML = `Answer = ${response['answer']}`;
        }
        el('answer-button').innerHTML = 'Answer';
    }

    var fileData = new FormData();
    fileData.append('article', article_text);
    fileData.append('question', question_text);
    xhr.send(fileData);
}
