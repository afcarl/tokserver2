//Load libraries using plain JavaScript
// (function(){
//     // TODO: an array
// //    theurl = "http://ajax.googleapis.com/ajax/libs/mootools/1.2.4/mootools-yui-compressed.js";
//     theurl = "https://code.jquery.com/jquery-2.1.4.min.js";
//     var newscript = document.createElement('script');
//     newscript.type = 'text/javascript';
//     newscript.async = true;
//     newscript.src = theurl;
//     (document.getElementsByTagName('head')[0]||document.getElementsByTagName('body')[0]).appendChild(newscript);
// })();


// unicode is broken in javascript!
// https://mathiasbynens.be/notes/javascript-unicode
// fix?
// https://github.com/lautis/unicode-substring


// random wikipedia:
// 1) get random language by parsing the table here:
// https://meta.wikimedia.org/wiki/List_of_Wikipedias/Table


// 2) get random page from that language:
// https://en.wikipedia.org/w/api.php?action=query&list=random&rnlimit=1&rnnamespace=0
// sub in lang for en.
// get an extract of the page id
//https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&pageids=21591234
//https://en.wikipedia.org/w/api.php?action=query&prop=extracts&pageids=21591234
// strip it of markup

var HOST="http://colo-vm4.isi.edu";
var PORT="8081";
var HOSTPORT=HOST+":"+PORT+"/";

function addelement(kind, idval, theparent) {
    var ret = document.createElement(kind);
//    console.log(ret)
    ret.setAttribute("id", idval);
//    console.log(ret)
    theparent.appendChild(ret);
//    console.log(theparent)
    return ret;
}
function nd(idval, theparent) {
    return addelement("div", idval, theparent);
}

function addtokrow(data, diffcodes, name, table) {
    var rowtag = nd("row", table);
    var labeltag = nd("left", rowtag);
    labeltag.textContent=name;
    var datatag = nd("right", rowtag);
    for(var i = 0; i < diffcodes.length; i++) {
        var code = diffcodes[i];
        var subtag = ""
//        var snippet = data.substring(parseInt(code[3]), parseInt(code[4]));
        var snippet = code[5];
        if (code[0] == "equal") {
            subtag = nd("plain", datatag);
        }
        // TODO: what if not insert?
        else {
            subtag = nd("markup", datatag);
        }
        subtag.appendChild(document.createTextNode(snippet));
    }
    //datatag.textContent=data;
    //console.log(diffcodes);
}
    

// can put 'json' as argument after function but doesn't seem necessary
// can be 'get' or 'getJSON'
// seems to be nondeterministic whether the data loads
function tokenize() {
    var div = document.getElementById("anchor");
    // clear the anchor
    while (div.firstChild) {
        div.removeChild(div.firstChild);
    }
    div.textContent="";

    var langs = [];
    var elems = document.getElementById("main").elements;
    for(var i = 0; i < elems.length; i++) {
        if(elems[i].type=="checkbox" && elems[i].checked) {
            langs.push(elems[i].value);
        }
    }
    

    var langlen = langs.length;
    for (var l = 0; l < langlen; l++) {
        $.get( HOSTPORT+langs[l]+"_20160103", function( data ) {
            var dl = data['data']['length'];
            var table = nd("container", div);
            for (var i = 0; i < dl; i++) {
                // TODO: for each tokenization...
                addtokrow(data['data']['original'][i], data['diffs']['original'][i], "original", table);
                addtokrow(data['data']['utok'][i], data['diffs']['utok'][i], "unitok 1.0", table);
                addtokrow(data['data']['twokenize'][i], data['diffs']['twokenize'][i], "CMU twok", table);
                addtokrow(data['data']['cdectok'][i], data['diffs']['cdectok'][i], "CMU cdectok", table);
            }
        }, 'json');
    }

}

function randwiktok() {
    wiktok('random');
}

function choosewiktok() {
    var lang = document.getElementById("lang").value;
    console.log(lang)
    if (lang == "")
        wiktok('random');
    else {
        // TODO: graceful if bad code
        wiktok(lang);
    }
}

function wiktok(langchoice) {
    var argdict = {};
    var numbox = document.getElementById("numbut");
    argdict['items']=numbox.value;
    argdict['lang']=langchoice;
    texttok(argdict);
}

function usertok() {
    var usertextbox = document.getElementById("usertextbox");
    var argdict = {};
    argdict['usertext']=usertextbox.value;
    texttok(argdict);
}

function texttok(argumentdict) {

    var div = document.getElementById("anchor");
    // clear the anchor
    while (div.firstChild) {
        div.removeChild(div.firstChild);
    }
    div.textContent="";
//    var numbox = document.getElementById("numbut");
    $.ajax({ 
        url: HOSTPORT+"wik", 
        data: argumentdict,
//        data: {'items':numbox.value, 'lang':langchoice}, 
        success: function( data ) {
            var table = nd("container", div);
            for (var i = 0; i< data.length; i++) {
                lang = data[i]['lang']+" ("+data[i]['isocode']+")";
                text = data[i]['text'];
                url = data[i]['url'];
                var row = nd("row", table);
                var label = nd("left", row);
                var urlitem = addelement("a", "url", label);
                urlitem.setAttribute("href", url);
                urlitem.textContent=lang;
                console.log(label)
                var datatag = nd("right", row);
                datatag.textContent=text;
                Object.keys(data[i]['tokenizations']).forEach(function (toktype) { 
                    var tokhash = data[i]['tokenizations'][toktype];
                    addtokrow(tokhash['data'], tokhash['diffs'], toktype, table);
                });
                var spacer = nd("blank_row", table);
                spacer.setAttribute("class", "blank_row");
            }
        },
        error: function( data ) {
            var table = nd("container", div);
            var row = nd("row", table);
            row.textContent="Something went wrong (bad lang code? glitch in the matrix?). Try again!"
        },
        
        dataType: 'json'
    });
}


