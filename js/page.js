const vp_width = window.innerWidth;

const addElement = (f, c) => {f.appendChild(c);};

const ErrorMsgs = {search_noresult:'Sua pesquisa não trouxe resultados.',error404:'Essa página não foi encontrada.'};

const params = new URLSearchParams(query_string);
var idValueUrl = params.get('id');
const pageUrl = "page.html?id=";
const pageUrlId = pageUrl + idValueUrl; 

var isearch = document.getElementById("isearch");

var card_attr = ['card', 'w-50', 'border-danger', 'border-1','text-danger', 'mx-auto', 'shadow-lg', 'mt-3']; //array bootstrap card classes

var alert = document.getElementById("alert_"); //ALERT SEARCH NO RESULT 
var alert_attr = ['alert', 'hidden_', 'alert-primary', 'd-flex', 'align-items-center', 'rounded-1', 'mx-auto', 'w-50'];
alert.setAttribute("class", alert_attr[0]);
var alert_span_msg = document.getElementById("alert_msg");

var nav = document.getElementById("nav"); 
var nav_attr = ['sticky-top', 'navbar', 'navbar-expand-lg', 'navbar-light', 'bg-light', 'text-danger', 'shadow-sm']; //nav bootstrap classes
nav.setAttribute("class", nav_attr[0]);

if (vp_width > 768) { //MOBILE RESPONSIVO
    nav_attr.splice(6, 0, 'rounded-1', 'mx-2', 'mt-2', 'mb-2');
    for (j = 1; j < nav_attr.length; j++) {
        nav.classList.add(nav_attr[j]);
        alert.classList.add(alert_attr[j]);
    } 
} else {
    card_attr[1] = 'w-100';
    alert_attr[7] = 'w-100';
    for (j = 1; j < nav_attr.length; j++) {
        nav.classList.add(nav_attr[j]);
        alert.classList.add(alert_attr[j]);
    }
    alert.classList.add('mt-3'); 
}

const load_content = function() {
    for (i = 0; i < x.length; i++) {
        //recupera conteúdo dos artigos
        const artigo = {id:x[i]._id, titulo:x[i]._titulo, content:x[i]._conteudo, data:x[i]._data, hora:x[i]._hora, author:x[i]._autor, imgsrc:x[i]._imgsrc, imgwth:x[i]._imgwth, imghgt:x[i]._imghgt};
        
        if (idValueUrl == artigo.id) {
            i = 51;
            console.log('id encontrado');
            console.log('i:', i)
            console.log(pageUrlId);
            var divmain = document.getElementById("_artigos"); //HTML MAIN

            var divcards = document.createElement("div"); //BOOTSTRAP CARD
            divcards.setAttribute("class", card_attr[0]);
            var id_atrr = "card_" + artigo.id; 
            divcards.setAttribute("id", id_atrr);
            for (j = 1; j < card_attr.length; j++) {
                divcards.classList.add(card_attr[j]);
            }
        
            var cardheader = document.createElement("div"); //CARD HEADER
            cardheader.setAttribute("class", "card-header");

            var h5title = document.createElement("h5"); //CARD TITLE
            h5title.setAttribute("class", "card-title");
            var link_title = document.createElement("a"); //LINK TITLE 
            link_title.setAttribute("class", "link-danger")
            link_title.setAttribute("href", pageUrl + artigo.id);
            var ctitle = document.createTextNode(artigo.titulo);

            var img = document.createElement("img"); //IMAGEM DO ARTIGO
            img.setAttribute("class", "card-img-top");
            img.setAttribute("src", artigo.imgsrc);

            var divcontent = document.createElement("div");
            divcontent.setAttribute("class", "card-body");
            var textcontent = document.createTextNode(artigo.content);

            var disqus_div = document.createElement("div");
            disqus_div.setAttribute("id", "disqus_thread");

            var cardfooter = document.createElement("footer");
            cardfooter.setAttribute("class", "card-footer");
            cardfooter.classList.add("text-muted");

            var divrow = document.createElement("div");
            divrow.setAttribute("class", "row");
            var divcol = document.createElement("div");
            divcol.setAttribute("class", "col");
            var divcol2 = document.createElement("div");
            divcol2.setAttribute("class", "col");
            

            var spandate = document.createElement("span");
            spandate.setAttribute("id", "date_");
            var contentdate = document.createTextNode(artigo.data);

            var spantime = document.createElement("span");
            spantime.setAttribute("id", "time_");
            spantime.setAttribute("class", "ms-1")
            var contenttime = document.createTextNode(artigo.hora);

            var divauthor = document.createElement("div");
            divauthor.setAttribute("class", "text-end");
            var spanauthor = document.createElement("span");
            spanauthor.setAttribute("id", "author_")
            var contentauthor = document.createTextNode(artigo.author);

            //divmain.appendChild(divcards);

            addElement(divmain, divcards); //ADD BOOTSTRAP CARD > HTML MAIN

            //divcards.appendChild(cardheader);

            addElement(divcards, cardheader);//ADD CARD HEADER

            if (artigo.imgsrc != 'None') {
                //divcards.appendChild(img);
                addElement(divcards, img); //ADD IMG
            }

            const elements = [divmain, divcards, divcards, cardheader, h5title, ctitle, divcards, divcontent,  textcontent, divcards, cardfooter, divrow, divcol, divrow, divcol2, divcol, spandate, divcol, spantime, spandate, contentdate, spantime, contenttime, divcol2, divauthor, spanauthor, contentauthor];

            //cardheader.appendChild(h5title);
            
            addElement(cardheader, h5title);//ADD HTML TITLE
            
            //h5title.appendChild(ctitle);
            
            addElement(h5title, link_title);
            addElement(link_title, ctitle)//ADD CONTENT TITLE

            //divcards.appendChild(divcontent);
            
            addElement(divcards, divcontent); //add content div
            
            //divcontent.appendChild(textcontent);
            
            addElement(divcontent, textcontent); //add content

            //divcards.appendChild(cardfooter);

            addElement(divcards, disqus_div);

            //ADD FOOTER
            addElement(divcards, cardfooter);
            addElement(cardfooter, divrow);
            addElement(divrow, divcol);
            addElement(divrow, divcol2);
            addElement(divcol, spandate);
            addElement(divcol, spantime);
            addElement(spandate, contentdate);
            addElement(spantime, contenttime);
            addElement(divcol2, divauthor);
            addElement(divauthor, spanauthor);
            addElement(spanauthor, contentauthor);
        } else if (i == x.length-1) {
            alert_span_msg.innerHTML = ErrorMsgs.error404;
            alert.classList.remove("hidden_");
            console.log(ErrorMsgs.error404);
        }     
    }
};
var toggler = document.getElementById("navbarSupportedContent");
var ver = toggler.classList.contains("navbar-collapse");
function undo() {
    console.log(toggler);
    console.log(ver);
    if (ver == true) {
        toggler.classList.remove("show");
        console.log('removendo...');
    }
}