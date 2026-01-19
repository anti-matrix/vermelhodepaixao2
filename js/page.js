// Configuration
const vp_width = window.innerWidth;
const addElement = (f, c) => { f.appendChild(c); };
const ErrorMsgs = {
    search_noresult: 'Sua pesquisa não trouxe resultados.',
    error404: 'Artigo não encontrado. O link pode estar incorreto ou o artigo foi removido.'
};

// Get ID from URL
const params = new URLSearchParams(query_string);
var idValueUrl = params.get('id');

// DOM Elements
var alert = document.getElementById("alert_");
var alert_span_msg = document.getElementById("alert_msg");
var nav = document.getElementById("nav");

// Responsive styling
var card_attr = ['card', 'w-50', 'border-danger', 'border-1', 'text-danger', 'mx-auto', 'shadow-lg', 'mt-3'];
var alert_attr = ['alert', 'hidden_', 'alert-primary', 'd-flex', 'align-items-center', 'rounded-1', 'mx-auto', 'w-50'];
var nav_attr = ['sticky-top', 'navbar', 'navbar-expand-lg', 'navbar-light', 'bg-light', 'text-danger', 'shadow-sm'];

// Apply initial classes
alert.setAttribute("class", alert_attr[0]);
nav.setAttribute("class", nav_attr[0]);

// Responsive adjustments
if (vp_width > 768) {
    nav_attr.splice(6, 0, 'rounded-1', 'mx-2', 'mt-2', 'mb-2');
    for (let j = 1; j < nav_attr.length; j++) {
        nav.classList.add(nav_attr[j]);
        alert.classList.add(alert_attr[j]);
    }
} else {
    card_attr[1] = 'w-100';
    alert_attr[7] = 'w-100';
    for (let j = 1; j < nav_attr.length; j++) {
        nav.classList.add(nav_attr[j]);
        alert.classList.add(alert_attr[j]);
    }
    alert.classList.add('mt-3');
}

// Create a single post view
function createPostView(artigo) {
    var divmain = document.getElementById("_artigos");
    
    // Clear any existing content
    divmain.innerHTML = '';
    
    // Create card container
    var divcards = document.createElement("div");
    divcards.setAttribute("class", card_attr[0]);
    var id_attr = "card_" + artigo.id;
    divcards.setAttribute("id", id_attr);
    for (let j = 1; j < card_attr.length; j++) {
        divcards.classList.add(card_attr[j]);
    }
    
    // Card header with title
    var cardheader = document.createElement("div");
    cardheader.setAttribute("class", "card-header");
    
    var h5title = document.createElement("h1"); // Changed to h1 for better SEO
    h5title.setAttribute("class", "card-title h3 mb-0");
    
    var ctitle = document.createTextNode(artigo.titulo);
    
    // Card body with full content
    var divcontent = document.createElement("div");
    divcontent.setAttribute("class", "card-body");
    
    // Preserve line breaks in content
    var contentParagraphs = artigo.content.split('\n').filter(p => p.trim() !== '');
    var contentContainer = document.createElement("div");
    
    contentParagraphs.forEach(paragraph => {
        var p = document.createElement("p");
        p.setAttribute("class", "mb-3");
        p.textContent = paragraph;
        contentContainer.appendChild(p);
    });
    
    // Card footer with metadata
    var cardfooter = document.createElement("footer");
    cardfooter.setAttribute("class", "card-footer text-muted bg-light");
    
    var divrow = document.createElement("div");
    divrow.setAttribute("class", "row");
    
    var divcol = document.createElement("div");
    divcol.setAttribute("class", "col-md-8");
    
    var divcol2 = document.createElement("div");
    divcol2.setAttribute("class", "col-md-4");
    
    var spandate = document.createElement("span");
    spandate.setAttribute("id", "date_");
    spandate.setAttribute("class", "me-3");
    var contentdate = document.createTextNode(artigo.data);
    
    var spantime = document.createElement("span");
    spantime.setAttribute("id", "time_");
    spantime.setAttribute("class", "me-3");
    var contenttime = document.createTextNode(artigo.hora);
    
    var divauthor = document.createElement("div");
    divauthor.setAttribute("class", "text-end");
    var spanauthor = document.createElement("span");
    spanauthor.setAttribute("id", "author_");
    var contentauthor = document.createTextNode("Por: " + artigo.author);
    
    // Set page title
    document.title = artigo.titulo + " - Vermelho de Paixão Archive";
    
    // Assemble the card
    addElement(divmain, divcards);
    addElement(divcards, cardheader);
    addElement(cardheader, h5title);
    addElement(h5title, ctitle);
    
    // Add image if available
    if (artigo.imgsrc && artigo.imgsrc !== 'None') {
        try {
            var imgWrapper = document.createElement("div");
            imgWrapper.setAttribute("class", "img-container text-center my-3");
            
            var img = document.createElement("img");
            img.setAttribute("class", "card-img-top img-fluid");
            img.setAttribute("src", artigo.imgsrc);
            img.setAttribute("alt", artigo.titulo.substring(0, 100));
            img.setAttribute("loading", "lazy");
            
            if (artigo.imgwth && artigo.imgwth !== 'None' && !isNaN(artigo.imgwth) && artigo.imgwth > 0) {
                img.setAttribute("width", artigo.imgwth);
            }
            if (artigo.imghgt && artigo.imghgt !== 'None' && !isNaN(artigo.imghgt) && artigo.imghgt > 0) {
                img.setAttribute("height", artigo.imghgt);
            }
            
            addElement(imgWrapper, img);
            
            // Insert image after header
            if (cardheader.nextSibling) {
                cardheader.parentNode.insertBefore(imgWrapper, cardheader.nextSibling);
            } else {
                addElement(divcards, imgWrapper);
            }
        } catch (e) {
            console.log("Error loading image:", e);
        }
    }
    
    addElement(divcards, divcontent);
    addElement(divcontent, contentContainer);
    addElement(divcards, cardfooter);
    addElement(cardfooter, divrow);
    addElement(divrow, divcol);
    addElement(divrow, divcol2);
    addElement(divcol, spandate);
    addElement(spandate, contentdate);
    addElement(divcol, spantime);
    addElement(spantime, contenttime);
    addElement(divcol2, divauthor);
    addElement(divauthor, spanauthor);
    addElement(spanauthor, contentauthor);
    
    // Add back button
    // var backButton = document.createElement("a");
    //backButton.setAttribute("href", "index.html");
    //backButton.setAttribute("class", "btn btn-outline-danger btn-sm mt-3");
    //backButton.innerHTML = '<i class="bi bi-arrow-left"></i> Voltar para todos os artigos';
    
    //var buttonContainer = document.createElement("div");
    //buttonContainer.setAttribute("class", "text-center mb-4");
    //addElement(buttonContainer, backButton);
    
    //if (divmain.firstChild) {
    //    divmain.insertBefore(buttonContainer, divmain.firstChild);
    //} else {
    //    addElement(divmain, buttonContainer);
    //}
    
    // Initialize Disqus comments
    initializeDisqus(artigo.id);
    
    return divcards;
}

// Initialize Disqus comments
function initializeDisqus(postId) {
    if (typeof DISQUS !== 'undefined') {
        DISQUS.reset({
            reload: true,
            config: function () {
                this.page.url = window.location.href;
                this.page.identifier = 'post_' + postId;
                this.page.title = document.title;
            }
        });
    } else {
        // First time loading Disqus
        window.disqus_config = function () {
            this.page.url = window.location.href;
            this.page.identifier = 'post_' + postId;
            this.page.title = document.title;
        };
        
        (function() {
            var d = document, s = d.createElement('script');
            s.src = 'https://vermelhodepaixao2.disqus.com/embed.js';
            s.setAttribute('data-timestamp', +new Date());
            (d.head || d.body).appendChild(s);
        })();
    }
}

// Find and display post by ID
function loadPostById(postId) {
    if (!postId) {
        showError(ErrorMsgs.error404);
        return;
    }
    
    // Convert postId to number if it's a string
    const numericId = parseInt(postId);
    if (isNaN(numericId)) {
        showError(ErrorMsgs.error404);
        return;
    }
    
    // Find the post
    const post = x.find(item => item._id === numericId);
    
    if (post) {
        console.log('Post encontrado:', post._id, post._titulo);
        
        const artigo = {
            id: post._id,
            titulo: post._titulo,
            content: post._conteudo,
            data: post._data,
            hora: post._hora,
            author: post._autor,
            imgsrc: post._imgsrc,
            imgwth: post._imgwth,
            imghgt: post._imghgt
        };
        
        createPostView(artigo);
        
        // Hide any error alerts
        alert.classList.add("hidden_");
    } else {
        console.log('Post não encontrado para ID:', postId);
        showError(ErrorMsgs.error404);
    }
}

// Show error message
function showError(message) {
    alert_span_msg.innerHTML = message;
    alert.classList.remove("hidden_");
    console.log(message);
    
    // Add a back button to index
    const main = document.getElementById("_artigos");
    main.innerHTML = '';
    
    const errorCard = document.createElement("div");
    errorCard.setAttribute("class", "card mx-auto mt-5");
    errorCard.style.maxWidth = "500px";
    
    errorCard.innerHTML = `
        <div class="card-body text-center">
            <h5 class="card-title text-danger">Artigo não encontrado</h5>
            <p class="card-text">${message}</p>
            <a href="index.html" class="btn btn-danger">
                <i class="bi bi-house-door"></i> Voltar para a página inicial
            </a>
        </div>
    `;
    
    addElement(main, errorCard);
}

// Load content when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Carregando artigo com ID:', idValueUrl);
    
    if (typeof x !== 'undefined' && Array.isArray(x)) {
        console.log(`Base de dados carregada: ${x.length} artigos disponíveis`);
        loadPostById(idValueUrl);
    } else {
        console.error('Erro: Array de artigos (x) não carregado');
        showError('Erro ao carregar os artigos. Por favor, recarregue a página.');
    }
});

// Handle search form submission
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('form[action="index.html"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('isearch');
            if (searchInput && searchInput.value.trim()) {
                // Redirect to index.html with search parameter
                this.action = `index.html?search=${encodeURIComponent(searchInput.value.trim())}`;
            } else {
                this.action = 'index.html';
            }
        });
    }
});