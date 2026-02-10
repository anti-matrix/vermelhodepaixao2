// vdpgpt.js - FIXED VERSION (No article duplication)

// Configuration
const vp_width = window.innerWidth;
const addElement = (f, c) => { f.appendChild(c); };
const ErrorMsgs = { 
    search_noresult: 'Sua pesquisa não trouxe resultados.',
    generation_error: 'Erro ao gerar artigo. Tente novamente.',
    no_query: 'Por favor, digite um tópico para gerar artigos.',
    generating: 'Gerando artigos...',
    success: 'Artigo(s) gerado(s) com sucesso!'
};
const pageUrl = "xpage.html?id=";

// API Configuration
const API_ENDPOINT = 'https://vermelhodepaixaox.onrender.com/api/generate';
const LOCAL_API_ENDPOINT = 'http://localhost:5000/api/generate'; // Alternative localhost

// DOM Elements
var isearch = document.getElementById("isearch");
var alert = document.getElementById("alert_");
var alert_span_msg = document.getElementById("alert_msg");
var generation_status = document.getElementById("generation_status");
var generation_message = document.getElementById("generation_message");
var nav = document.getElementById("nav");

// Initialize error messages
alert_span_msg.innerHTML = ErrorMsgs.search_noresult;

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

// ==================== ARTICLE FUNCTIONS ====================

// Helper function to add image if available
function addImageIfAvailable(artigo, container) {
    if (artigo.imgsrc && artigo.imgsrc !== 'None') {
        try {
            var img = document.createElement("img");
            img.setAttribute("class", "card-img-top mt-2 mb-2");
            img.setAttribute("src", artigo.imgsrc);
            img.setAttribute("alt", artigo.titulo.substring(0, 50));
            img.setAttribute("loading", "lazy");
            if (artigo.imgwth && artigo.imgwth !== 'None') {
                img.setAttribute("width", artigo.imgwth);
            }
            if (artigo.imghgt && artigo.imghgt !== 'None') {
                img.setAttribute("height", artigo.imghgt);
            }
            addElement(container, img);
        } catch (e) {
            console.log("Error loading image:", e);
        }
    }
}

// Helper function to extract YouTube video ID
function extractYouTubeVideoId(url) {
    if (!url) return null;
    
    const patterns = [
        /(?:youtube\.com\/embed\/)([^?&]+)/,
        /(?:youtu\.be\/)([^?&]+)/,
        /(?:youtube\.com\/watch\?v=)([^?&]+)/,
        /(?:youtube\.com\/v\/)([^?&]+)/,
        /(?:youtube\.com\/embed\/)([^?&]+)/
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) return match[1];
    }
    
    return null;
}

// Helper function to create proper YouTube embed URL
function createYouTubeEmbedUrl(videoId, options = {}) {
    if (!videoId) return null;
    
    let embedUrl = `https://www.youtube.com/embed/${videoId}`;
    const params = [];
    
    if (options.autoplay) params.push('autoplay=1');
    if (options.loop) params.push('loop=1');
    if (options.controls === false) params.push('controls=0');
    if (options.modestbranding) params.push('modestbranding=1');
    
    if (params.length > 0) {
        embedUrl += '?' + params.join('&');
    }
    
    return embedUrl;
}

// Updated function to handle video embeds more robustly
function createVideoEmbed(videosrc, videowth, videohgt, title) {
    if (!videosrc || videosrc === 'None') return null;
    
    // Check if it's a YouTube URL
    const videoId = extractYouTubeVideoId(videosrc);
    
    if (videoId) {
        // Create YouTube embed URL with proper parameters
        const embedUrl = createYouTubeEmbedUrl(videoId, {
            modestbranding: true,
            controls: true,
            autoplay: false
        });
        
        const videoContainer = document.createElement("div");
        videoContainer.setAttribute("class", "embed-responsive embed-responsive-16by9 mt-2 mb-2");
        
        const iframe = document.createElement("iframe");
        iframe.setAttribute("class", "embed-responsive-item");
        iframe.setAttribute("src", embedUrl);
        iframe.setAttribute("title", title);
        iframe.setAttribute("frameborder", "0");
        iframe.setAttribute("allowfullscreen", "");
        iframe.setAttribute("allow", "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture");
        
        // Set responsive width/height
        iframe.setAttribute("width", "100%");
        iframe.setAttribute("height", "100%");
        
        videoContainer.appendChild(iframe);
        return videoContainer;
    }
    
    // Handle other video sources (if needed in the future)
    return null;
}

// Create a single post card - MODIFIED TO NOT AUTO-APPEND
function createPostCard(artigo, shouldAppend = true) {
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
    
    var textcontent = document.createTextNode(artigo.content);
    
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
    
    // Assemble the card (but don't append automatically)
    if (shouldAppend) {
        addElement(divmain, divcards);
    }
    
    addElement(divcards, cardheader);
    addElement(cardheader, h5title);
    addElement(h5title, link_title);
    addElement(link_title, ctitle);
    
    // Add video if available (priority over image)
    if (artigo.videosrc && artigo.videosrc !== 'None' && artigo.videosrc !== '') {
        try {
            const videoEmbed = createVideoEmbed(
                artigo.videosrc,
                artigo.videowth,
                artigo.videohgt,
                artigo.titulo.substring(0, 50)
            );
            
            if (videoEmbed) {
                addElement(divcards, videoEmbed);
            } else {
                // Fall back to image if video creation fails
                addImageIfAvailable(artigo, divcards);
            }
        } catch (e) {
            console.log("Error loading video:", e);
            // Fall back to image if video fails
            addImageIfAvailable(artigo, divcards);
        }
    } else {
        // Add image if available (only if no video)
        addImageIfAvailable(artigo, divcards);
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

// Load a batch of posts - UPDATED TO HANDLE BOTH GENERATED AND OLD ARTICLES
function loadPostsBatch(startIndex, batchSize) {
    const postsContainer = document.getElementById("_artigos");
    const postsToLoad = filteredPosts || allArticles;
    
    const endIndex = Math.min(startIndex + batchSize, postsToLoad.length);
    
    for (let i = startIndex; i < endIndex; i++) {
        const artigo = postsToLoad[i];
        
        // Create the card using the existing createPostCard function
        createPostCard(artigo);
    }
    
    return endIndex;
}

// Create and display a single generated article immediately - FIXED VERSION
function displaySingleGeneratedArticle(article, index, total, generationInfo = {}) {
    // Clean the title by removing "**TÍTULO:**", "TÍTULO:", and similar patterns
    let cleanedTitle = article._titulo || '';
    
    // Clean common erroneous patterns from title
    cleanedTitle = cleanedTitle
        .replace(/^\*\*TÍTULO:\*\*\s*/i, '')  // Remove **TÍTULO:** at start
        .replace(/^\*\*TITULO:\*\*\s*/i, '')   // Remove **TITULO:** at start  
        .replace(/^TÍTULO:\s*/i, '')           // Remove TÍTULO: at start
        .replace(/^TITULO:\s*/i, '')           // Remove TITULO: at start
        .replace(/^\*\*TÍTULO \*\*\s*/i, '')   // Remove **TÍTULO ** at start
        .replace(/^\*\*TITULO \*\*\s*/i, '')   // Remove **TITULO ** at start
        .replace(/^TÍTULO \s*/i, '')           // Remove TÍTULO  at start
        .replace(/^TITULO \s*/i, '')           // Remove TITULO  at start
        .replace(/^\*\*/, '')                  // Remove remaining ** at start
        .replace(/\*\*$/, '')                  // Remove ** at end
        .trim();
    
    // Check if it's "artigo gerado" case
    const isArtigoGerado = cleanedTitle.toLowerCase().includes('artigo gerado') || 
                          cleanedTitle.toLowerCase() === 'artigo' ||
                          cleanedTitle.trim() === '';
    
    // If it's "artigo gerado", don't display it
    if (isArtigoGerado) {
        console.log(`⏭️  Pulando artigo ${index + 1}/${total}: "${article._titulo?.substring(0, 50)}..."`);
        console.log(`   Modelo usado: ${generationInfo.model || 'N/A'}`);
        console.log(`   Motivo: Título inválido ("Artigo Gerado")`);
        return; // Skip displaying this article
    }
    
    // Clean common erroneous patterns from content
    let cleanedContent = article._conteudo || '';
    cleanedContent = cleanedContent
        .replace(/^\*\*CONTEÚDO:\*\*\s*/i, '')  // Remove **CONTEÚDO:** at start
        .replace(/^\*\*CONTEUDO:\*\*\s*/i, '')   // Remove **CONTEUDO:** at start
        .replace(/^CONTEÚDO:\s*/i, '')          // Remove CONTEÚDO: at start
        .replace(/^CONTEUDO:\s*/i, '')          // Remove CONTEUDO: at start
        .trim();
    
    // If title is still empty after cleaning, don't display
    if (!cleanedTitle || cleanedTitle.length < 5) {
        console.log(`⏭️  Pulando artigo ${index + 1}/${total}: Título muito curto após limpeza`);
        console.log(`   Título após limpeza: "${cleanedTitle}"`);
        return; // Skip displaying this article
    }
    
    // If content is still empty after cleaning, use the original
    if (!cleanedContent) {
        cleanedContent = article._conteudo || '';
    }
    
    // Log what was cleaned (only if it was actually cleaned)
    if (cleanedTitle !== article._titulo) {
        console.log(`🧹 Artigo ${index + 1}/${total}: Título limpo`);
        console.log(`   Original: "${article._titulo?.substring(0, 50)}..."`);
        console.log(`   Limpo: "${cleanedTitle.substring(0, 50)}..."`);
    }
    
    // Create article object with cleaned data
    const artigo = {
        id: article._id,
        titulo: cleanedTitle,
        content: cleanedContent,
        data: article._data,
        hora: article._hora,
        author: article._autor,
        imgsrc: article._imgsrc,
        imgwth: article._imgwth,
        imghgt: article._imghgt,
        videosrc: article._videosrc || 'None',
        videowth: article._videowth || 'None',
        videohgt: article._videohgt || 'None'
    };
    
    // Check if this article already exists in allArticles to prevent duplicates
    const articleExists = allArticles.some(existingArticle => 
        existingArticle.id === artigo.id || 
        existingArticle.titulo === artigo.titulo
    );
    
    if (articleExists) {
        console.log(`⏭️  Artigo ${index + 1}/${total} já existe, pulando duplicata`);
        return;
    }
    
    // Add to beginning of allArticles array - BUT DON'T RELOAD ALL ARTICLES
    allArticles.unshift(artigo);
    
    // Get posts container
    const postsContainer = document.getElementById("_artigos");
    
    // Create the card and manually insert it at the top
    const cardElement = createPostCard(artigo, false); // Create but don't append
    if (postsContainer.firstChild) {
        postsContainer.insertBefore(cardElement, postsContainer.firstChild);
    } else {
        postsContainer.appendChild(cardElement);
    }
    
    // Log generation details for this specific article
    console.log(`✅ Artigo ${index + 1}/${total}: "${artigo.titulo.substring(0, 50)}..."`);
    console.log(`   Modelo usado: ${generationInfo.model || 'N/A'}`);
    if (article._response_time) {
        console.log(`   Tempo de geração no servidor: ${article._response_time.toFixed(2)}s`);
    }
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

// Show/hide generation status
function showGenerationStatus(show, message = ErrorMsgs.generating) {
    if (generation_status && generation_message) {
        if (show) {
            //generation_message.textContent = message;
            generation_status.classList.remove("hidden_");
        } else {
            generation_status.classList.add("hidden_");
        }
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    if (alert && alert_span_msg) {
        alert_span_msg.innerHTML = message;
        alert.classList.remove("hidden_");
        
        // Change alert class based on type
        alert.className = 'alert d-flex align-items-center rounded-1 mx-auto w-50';
        if (type === 'success') {
            alert.classList.add('alert-success');
        } else if (type === 'warning') {
            alert.classList.add('alert-warning');
        } else if (type === 'error' || type === 'danger') {
            alert.classList.add('alert-danger');
        } else {
            alert.classList.add('alert-primary');
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            alert.classList.add("hidden_");
        }, 5000);
    }
}

// Check if we need to load more posts
function checkScroll() {
    if (isLoading || !hasMore) return;
    
    const postsToLoad = filteredPosts || allArticles;
    const scrollPosition = window.innerHeight + window.scrollY;
    const pageHeight = document.documentElement.scrollHeight;
    const threshold = 500;
    
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
    
    setTimeout(() => {
        const postsToLoad = filteredPosts || allArticles;
        const startIndex = currentPage * postsPerPage;
        
        if (startIndex < postsToLoad.length) {
            const endIndex = loadPostsBatch(startIndex, postsPerPage);
            currentPage++;
            
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
    }, 300);
}

// Reset posts and reload from beginning
function resetPosts() {
    const postsContainer = document.getElementById("_artigos");
    postsContainer.innerHTML = '';
    
    currentPage = 0;
    isLoading = false;
    hasMore = true;
    
    showNoMorePosts(false);
    showLoading(false);
    loadMorePosts();
}

// Generate articles from query - ALL 3 AND DISPLAY ONE AT A TIME
async function generateArticles(query) {
    
    if (!query || query.trim() === '') {
        showAlert(ErrorMsgs.no_query, 'warning');
        return;
    }
    
    showGenerationStatus(true, ErrorMsgs.generating);
    
    try {
        // Record start time for client-side measurement
        const clientStartTime = Date.now();
        
        // Try both endpoints
        let endpoint = API_ENDPOINT;
        let response = null;
        
        try {
            console.log(`🚀 Iniciando geração de 3 artigos...`);
            console.log(`   Query: "${query}"`);
            console.log(`   Endpoint: ${endpoint}`);
            console.log(`   Timeout threshold do servidor: 25s`);
            console.log(`   Contagem solicitada: 3 artigos`);
            
            response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    count: 3  // Request 3 articles at once
                })
            });
        } catch (e) {
            // Try local endpoint
            endpoint = LOCAL_API_ENDPOINT;
            console.log(`   Tentando endpoint alternativo: ${endpoint}`);
            
            response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    count: 3  // Request 3 articles at once
                })
            });
        }
        
        // Calculate client-side time
        const clientEndTime = Date.now();
        const clientTotalTime = clientEndTime - clientStartTime;
        
        console.log(`📊 Estatísticas da requisição:`);
        console.log(`   HTTP Status: ${response.status}`);
        console.log(`   Tempo total da requisição (cliente): ${clientTotalTime}ms`);
        
        if (!response.ok) {
            console.error(`❌ Erro HTTP! status: ${response.status}`);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        console.log(`✅ Resposta recebida do servidor`);
        console.log(`   Sucesso: ${data.success}`);
        console.log(`   Modelo usado no servidor: ${data.model_used || 'N/A'}`);
        console.log(`   Total de artigos recebidos: ${data.articles ? data.articles.length : 0}`);
        
        if (data.rate_limited_models && data.rate_limited_models.length > 0) {
            console.log(`   Modelos com rate limit: ${data.rate_limited_models.join(', ')}`);
        }
        
        if (data.slow_models && data.slow_models.length > 0) {
            console.log(`   Modelos lentos: ${data.slow_models.join(', ')}`);
        }
        
        if (data.success && data.articles && data.articles.length > 0) {
            showGenerationStatus(false);
            
            console.log(`\n📈 RESUMO DA GERAÇÃO:`);
            console.log(`   Quantidade de artigos gerados: ${data.articles.length}`);
            console.log(`   Modelo final usado: ${data.model_used}`);
            console.log(`   Tempo total da requisição: ${clientTotalTime}ms`);
            console.log(`   Timeout threshold do servidor: 25s`);
            console.log(`   Status HTTP: 200 OK\n`);
            
            let displayedCount = 0;

            // Display each article one at a time with a small delay for better UX
            data.articles.forEach((article, index) => {
                console.log(`\n🖼️ DEBUG Article ${index + 1} Image Info:`);
                console.log(`   Title: ${article._titulo?.substring(0, 50)}...`);
                console.log(`   _imgsrc exists: ${!!article._imgsrc}`);
                console.log(`   _imgsrc value: ${article._imgsrc === 'None' ? 'None' : article._imgsrc?.substring(0, 80) + '...'}`);
                console.log(`   _imgsrc length: ${article._imgsrc?.length || 0}`);
                console.log(`   _imgwth: ${article._imgwth}`);
                console.log(`   _imghgt: ${article._imghgt}`);
                console.log(`   Is base64: ${article._imgsrc?.startsWith('data:image/') || false}`);
                
                // Add a small delay between displaying each article
                setTimeout(() => {
                    // Extract generation info from the article metadata
                    const generationInfo = {
                        model: article._model || data.model_used,
                        responseTime: article._response_time,
                        clientTime: clientTotalTime
                    };
                    
                    // Try to display the article (might skip if invalid)
                    displaySingleGeneratedArticle(article, index, data.articles.length, generationInfo);
                    
                    // If article was displayed, increment counter
                    if (!article._titulo.toLowerCase().includes('artigo gerado')) {
                        displayedCount++;
                    }
                    
                    // If this is the last article, show final summary
                    if (index === data.articles.length - 1) {
                        setTimeout(() => {
                            console.log(`🎉 GERAÇÃO COMPLETE!`);
                            console.log(`   Total de artigos recebidos: ${data.articles.length}`);
                            console.log(`   Artigos exibidos: ${displayedCount}`);
                            console.log(`   Artigos ignorados: ${data.articles.length - displayedCount}`);
                            console.log(`   Modelo final: ${data.model_used}`);
                            console.log(`   Tempo total: ${clientTotalTime}ms`);
                            console.log(`   Timeout threshold: 25s`);
                            console.log(`   Status: 200 OK`);
                            
                            // Show final alert only if at least one article was displayed
                            if (displayedCount > 0) {
                                showAlert(`${displayedCount} artigo(s) gerado(s) com sucesso!`, 'success');
                            } else {
                                showAlert('Nenhum artigo válido foi gerado. Tente novamente.', 'warning');
                            }
                        }, 500);
                    }
                }, index * 300); // 300ms delay between displaying each article
            });
            
        } else {
            showGenerationStatus(false);
            console.error(`❌ Falha na geração: ${data.error || ErrorMsgs.generation_error}`);
            showAlert(data.error || ErrorMsgs.generation_error, 'error');
        }
    } catch (error) {
        console.error('❌ Erro na geração:', error);
        showGenerationStatus(false);
        
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            console.error('   Servidor de geração não está respondendo');
            console.error('   Certifique-se de que o article_generator.py está rodando com --web');
            showAlert('Servidor de geração não está respondendo. Certifique-se de que o article_generator.py está rodando com --web', 'error');
        } else {
            console.error(`   Detalhes do erro: ${error.message}`);
            showAlert(ErrorMsgs.generation_error, 'error');
        }
    }
}

// Initialize search from URL
function initSearchFromUrl() {
    if (query_string && query_string !== "?" && query_string !== "?query=") {
        const params = new URLSearchParams(query_string);
        const queryValue = params.get('query');
        
        if (queryValue) {
            isearch.value = queryValue;
            generateArticles(queryValue);
        } else {
            resetPosts();
        }
    } else {
        resetPosts();
    }
}

// Debounced scroll handler
let scrollTimeout;
function debouncedCheckScroll() {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(checkScroll, 100);
}

// ==================== INITIALIZATION ====================

// Global variable to hold all articles (both old and generated)
let allArticles = [];

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Combine articles from both sources
    allArticles = [];
    
    // Add old articles from all_materias.js if available
    if (typeof x_old !== 'undefined' && Array.isArray(x_old)) {
        console.log(`Loaded ${x_old.length} old articles from all_materias.js`);
        
        // Convert old articles to the same format as generated articles
        x_old.forEach(oldArticle => {
            const artigo = {
                id: oldArticle._id,
                titulo: oldArticle._titulo,
                content: oldArticle._conteudo,
                data: oldArticle._data,
                hora: oldArticle._hora,
                author: oldArticle._autor,
                imgsrc: oldArticle._imgsrc,
                imgwth: oldArticle._imgwth,
                imghgt: oldArticle._imghgt,
                videosrc: oldArticle._videosrc || 'None',
                videowth: oldArticle._videowth || 'None',
                videohgt: oldArticle._videohgt || 'None'
            };
            allArticles.push(artigo);
        });
    } else {
        console.warn('Old articles (x_old) not found or not an array');
    }
    
    // Add generated articles from materias_generated.js if available
    if (typeof x !== 'undefined' && Array.isArray(x)) {
        console.log(`Loaded ${x.length} generated articles from materias_generated.js`);
        
        // Convert generated articles to the same format
        x.forEach(genArticle => {
            const artigo = {
                id: genArticle._id,
                titulo: genArticle._titulo,
                content: genArticle._conteudo,
                data: genArticle._data,
                hora: genArticle._hora,
                author: genArticle._autor,
                imgsrc: genArticle._imgsrc,
                imgwth: genArticle._imgwth,
                imghgt: genArticle._imghgt,
                videosrc: genArticle._videosrc || 'None',
                videowth: genArticle._videowth || 'None',
                videohgt: genArticle._videohgt || 'None'
            };
            allArticles.push(artigo);
        });
    } else {
        console.warn('Generated articles (x) not found or not an array');
    }
    
    // Sort articles by date (newest first)
    allArticles.sort((a, b) => {
        // Create date objects for comparison
        const dateA = new Date(a.data.split('/').reverse().join('-') + 'T' + a.hora);
        const dateB = new Date(b.data.split('/').reverse().join('-') + 'T' + b.hora);
        return dateB - dateA;
    });
    
    console.log(`Total articles loaded: ${allArticles.length}`);
    
    // Set up event listeners
    window.addEventListener('scroll', debouncedCheckScroll);
    
    // Search form handler (now generation form)
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = isearch.value.trim();
            if (query) {
                // Update URL with query parameter
                const url = new URL(window.location);
                url.searchParams.set('query', query);
                window.history.pushState({}, '', url);
                
                generateArticles(query);
            } else {
                showAlert(ErrorMsgs.no_query, 'warning');
            }
        });
    }
    
    // Initial load
    initSearchFromUrl();
});

// Handle browser back/forward buttons
window.addEventListener('popstate', function() {
    initSearchFromUrl();
});