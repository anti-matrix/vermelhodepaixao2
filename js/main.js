// Configuration
const vp_width = window.innerWidth;
const addElement = (f, c) => { f.appendChild(c); };
const ErrorMsgs = { search_noresult: 'Sua pesquisa não trouxe resultados.' };
const pageUrl = "page.html?id=";

// DOM Elements
var isearch = document.getElementById("isearch");
var alert = document.getElementById("alert_");
var alert_span_msg = document.getElementById("alert_msg");
alert_span_msg.innerHTML = ErrorMsgs.search_noresult;
var nav = document.getElementById("nav");

// Responsive styling
var card_attr = ['card', 'w-50', 'border-danger', 'border-1', 'text-danger', 'mx-auto', 'shadow-lg', 'mt-3'];
var alert_attr = ['alert', 'hidden_', 'alert-primary', 'd-flex', 'align-items-center', 'rounded-1', 'mx-auto', 'w-50'];
var nav_attr = ['sticky-top', 'navbar', 'navbar-expand-lg', 'navbar-light', 'bg-light', 'text-danger', 'shadow-sm'];

alert.setAttribute("class", alert_attr[0]);
nav.setAttribute("class", nav_attr[0]);

if (vp_width > 768) {
    nav_attr.splice(6, 0, 'rounded-1', 'mx-2', 'mt-2', 'mb-2');
    for (j = 1; j < nav_attr.length; j++) {
        nav.classList.add(nav_attr[j]);
        alert.classList.add(alert_attr[j]);
    }
} else {
    card_attr[1] = 'w-75';
    alert_attr[7] = 'w-75';
    for (j = 1; j < nav_attr.length; j++) {
        nav.classList.add(nav_attr[j]);
        alert.classList.add(alert_attr[j]);
    }
    alert.classList.add('mt-3');
}

// Create a single post card
function createPostCard(artigo) {
    var divmain = document.getElementById("_artigos");
    
    // Create card container
    var divcards = document.createElement("div");
    divcards.setAttribute("class", card_attr[0]);
    var id_attr = "card_" + artigo.id;
    divcards.setAttribute("id", id_attr);
    for (j = 1; j < card_attr.length; j++) {
        divcards.classList.add(card_attr[j]);
    }
    
    // Card header with title
    var cardheader = document.createElement("div");
    cardheader.setAttribute("class", "card-header");
    
    var h5title = document.createElement("h5");
    h5title.setAttribute("class", "card-title");
    
    var link_title = document.createElement("a");
    link_title.setAttribute("class", "link-danger");
    link_title.setAttribute("href", pageUrl + artigo.id);
    link_title.setAttribute("title", artigo.titulo);
    
    var ctitle = document.createTextNode(
        artigo.titulo.length > 100 ? 
        artigo.titulo.substring(0, 100) + "..." : 
        artigo.titulo
    );
    
    // Card body with content
    var divcontent = document.createElement("div");
    divcontent.setAttribute("class", "card-body");
    
    var contentPreview = artigo.content.length > 200 ?
        artigo.content.substring(0, 200) + "..." :
        artigo.content;
    var textcontent = document.createTextNode(contentPreview);
    
    // Card footer with metadata
    var cardfooter = document.createElement("footer");
    cardfooter.setAttribute("class", "card-footer text-muted");
    
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
    spantime.setAttribute("class", "ms-1");
    var contenttime = document.createTextNode(artigo.hora);
    
    var divauthor = document.createElement("div");
    divauthor.setAttribute("class", "text-end");
    var spanauthor = document.createElement("span");
    spanauthor.setAttribute("id", "author_");
    var contentauthor = document.createTextNode(artigo.author);
    
    // Assemble the card
    addElement(divmain, divcards);
    addElement(divcards, cardheader);
    addElement(cardheader, h5title);
    addElement(h5title, link_title);
    addElement(link_title, ctitle);
    
    // Add image if available
    if (artigo.imgsrc && artigo.imgsrc !== 'None') {
        try {
            var img = document.createElement("img");
            img.setAttribute("class", "card-img-top mt-2 mb-2");
            img.setAttribute("src", artigo.imgsrc);
            img.setAttribute("alt", artigo.titulo.substring(0, 50));
            img.setAttribute("loading", "lazy"); // Lazy load images
            if (artigo.imgwth && artigo.imgwth !== 'None') {
                img.setAttribute("width", artigo.imgwth);
            }
            if (artigo.imghgt && artigo.imghgt !== 'None') {
                img.setAttribute("height", artigo.imghgt);
            }
            addElement(divcards, img);
        } catch (e) {
            console.log("Error loading image:", e);
        }
    }
    
    addElement(divcards, divcontent);
    addElement(divcontent, textcontent);
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
    
    return divcards;
}

// Load a batch of posts
function loadPostsBatch(startIndex, batchSize) {
    const postsContainer = document.getElementById("_artigos");
    const postsToLoad = filteredPosts || x;
    
    const endIndex = Math.min(startIndex + batchSize, postsToLoad.length);
    
    for (let i = startIndex; i < endIndex; i++) {
        const artigo = {
            id: postsToLoad[i]._id,
            titulo: postsToLoad[i]._titulo,
            content: postsToLoad[i]._conteudo,
            data: postsToLoad[i]._data,
            hora: postsToLoad[i]._hora,
            author: postsToLoad[i]._autor,
            imgsrc: postsToLoad[i]._imgsrc,
            imgwth: postsToLoad[i]._imgwth,
            imghgt: postsToLoad[i]._imghgt
        };
        
        createPostCard(artigo);
    }
    
    return endIndex;
}

// Show/hide loading indicator
function showLoading(show) {
    const loading = document.getElementById("loadingIndicator");
    const noMore = document.getElementById("noMorePosts");
    
    if (show) {
        loading.classList.remove("hidden_");
        noMore.classList.add("hidden_");
    } else {
        loading.classList.add("hidden_");
    }
}

// Show/hide no more posts message
function showNoMorePosts(show) {
    const noMore = document.getElementById("noMorePosts");
    const loading = document.getElementById("loadingIndicator");
    
    if (show) {
        noMore.classList.remove("hidden_");
        loading.classList.add("hidden_");
    } else {
        noMore.classList.add("hidden_");
    }
}

// Check if we need to load more posts
function checkScroll() {
    if (isLoading || !hasMore) return;
    
    const postsToLoad = filteredPosts || x;
    const scrollPosition = window.innerHeight + window.scrollY;
    const pageHeight = document.documentElement.scrollHeight;
    const threshold = 500; // pixels from bottom
    
    if (scrollPosition >= pageHeight - threshold) {
        if (currentPage * postsPerPage < postsToLoad.length) {
            loadMorePosts();
        } else {
            hasMore = false;
            showNoMorePosts(true);
        }
    }
}

// Load more posts
function loadMorePosts() {
    if (isLoading) return;
    
    isLoading = true;
    showLoading(true);
    
    // Simulate loading delay for better UX
    setTimeout(() => {
        const postsToLoad = filteredPosts || x;
        const startIndex = currentPage * postsPerPage;
        
        if (startIndex < postsToLoad.length) {
            const endIndex = loadPostsBatch(startIndex, postsPerPage);
            currentPage++;
            
            // Update hasMore flag
            if (endIndex >= postsToLoad.length) {
                hasMore = false;
                showNoMorePosts(true);
            } else {
                showLoading(false);
            }
        } else {
            hasMore = false;
            showNoMorePosts(true);
        }
        
        isLoading = false;
    }, 300); // Small delay for better UX
}

// Perform search
function performSearch(searchTerm) {
    if (!searchTerm || searchTerm.trim() === '') {
        // Clear search
        filteredPosts = null;
        resetPosts();
        return;
    }
    
    const searchLower = searchTerm.toLowerCase();
    filteredPosts = x.filter(post => {
        return post._titulo.toLowerCase().includes(searchLower) ||
               post._conteudo.toLowerCase().includes(searchLower) ||
               post._autor.toLowerCase().includes(searchLower);
    });
    
    resetPosts();
    
    // Show no results message
    if (filteredPosts.length === 0) {
        alert.classList.remove("hidden_");
        alert_span_msg.innerHTML = ErrorMsgs.search_noresult;
    } else {
        alert.classList.add("hidden_");
    }
}

// Reset posts and reload from beginning
function resetPosts() {
    const postsContainer = document.getElementById("_artigos");
    postsContainer.innerHTML = '';
    
    currentPage = 0;
    isLoading = false;
    hasMore = true;
    
    showNoMorePosts(false);
    loadMorePosts(); // Load first batch
}

// Initialize search from URL
function initSearchFromUrl() {
    if (query_string && query_string !== "?" && query_string !== "?search=") {
        const params = new URLSearchParams(query_string);
        const searchValue = params.get('search');
        
        if (searchValue) {
            isearch.value = searchValue;
            performSearch(searchValue);
        } else {
            // Initial load
            resetPosts();
        }
    } else {
        // Initial load
        resetPosts();
    }
}

// Debounced scroll handler
let scrollTimeout;
function debouncedCheckScroll() {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(checkScroll, 100);
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    window.addEventListener('scroll', debouncedCheckScroll);
    
    // Search form handler
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            performSearch(isearch.value);
            
            // Update URL without reloading
            const url = new URL(window.location);
            if (isearch.value.trim()) {
                url.searchParams.set('search', isearch.value);
            } else {
                url.searchParams.delete('search');
            }
            window.history.pushState({}, '', url);
        });
    }
    
    // Clear search button (optional - you can add a clear button later)
    
    // Initial load
    if (typeof x !== 'undefined' && Array.isArray(x)) {
        console.log(`Loaded ${x.length} posts`);
        initSearchFromUrl();
    } else {
        console.error('Posts array (x) not found or not an array');
        document.getElementById("_artigos").innerHTML = 
            '<div class="alert alert-danger w-50 mx-auto mt-4">Erro ao carregar os artigos.</div>';
    }
});

// Handle browser back/forward buttons
window.addEventListener('popstate', function() {
    initSearchFromUrl();
});