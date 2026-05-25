document.addEventListener('DOMContentLoaded', () => {
    // --- Global Variable Declarations ---
    const mainNavbar = document.getElementById('main-navbar');
    const heroSection = document.getElementById('hero');
    const desktopMenuButton = document.getElementById('desktop-menu-button');
    const desktopNavOverlay = document.getElementById('desktop-nav-overlay');
    const desktopNavCloseButton = document.getElementById('desktop-nav-close-button');
    const backdropOverlay = document.getElementById('backdrop-overlay');

    const contactModal = document.getElementById("contactModal");
    const closeButton = document.getElementsByClassName("close")[0];
    const modalContactForm = document.getElementById("modal-contact-form");
    const confirmationMessage = document.getElementById("confirmation-message");
    const productInfoSpan = document.getElementById("product-info");

    const productGridContainer = document.getElementById('products');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const loadMoreBtn = document.getElementById('load-more-btn');
    const loadMoreContainer = document.getElementById('load-more-products-container');

    const cartIcon = document.querySelector('a.cart-link');
    const cartQuantitySpan = document.querySelector('.cart-badge');
    const cartModal = document.getElementById("cartModal");
    const closeCartModalButton = document.querySelector(".close-cart-modal");
    const cartItemsContainer = document.getElementById("cart-items-container");
    const emptyCartMessage = document.getElementById("empty-cart-message");
    const cartTotalPriceSpan = document.getElementById("cart-total-price");
    const requestQuoteFromCartBtn = document.getElementById("request-quote-from-cart-btn");

    const mainContactForm = document.getElementById('contact-form');
    const mainConfirmationMessage = document.getElementById('quote-confirmation-message');

    const desktopSearchInput = document.getElementById('desktop-search-input');
    const desktopSearchButton = document.getElementById('desktop-search-button');

    // --- Product data (populated from API) ---
    let allProductsData = [];

    const initialDisplayCount = 6;
    const productsPerLoad = 6;
    let visibleCounts = {};
    let activeFilter = 'todos los productos';
    let currentSearchTerm = '';

    // --- Navbar Sticky ---
    const heroObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                mainNavbar.classList.remove('sticky');
            } else {
                mainNavbar.classList.add('sticky');
            }
        });
    }, { rootMargin: '-50px 0px 0px 0px' });

    if (heroSection) heroObserver.observe(heroSection);

    // --- Off-Canvas Menu ---
    function openDesktopNav() {
        desktopNavOverlay.classList.add('active');
        backdropOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeDesktopNav() {
        desktopNavOverlay.classList.remove('active');
        backdropOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (desktopMenuButton) desktopMenuButton.addEventListener('click', openDesktopNav);
    if (desktopNavCloseButton) desktopNavCloseButton.addEventListener('click', closeDesktopNav);
    if (backdropOverlay) backdropOverlay.addEventListener('click', closeDesktopNav);

    desktopNavOverlay.querySelectorAll('ul li a').forEach(link => {
        link.addEventListener('click', closeDesktopNav);
    });

    // --- Dark / Light Mode ---
    const themeToggleCheckbox = document.getElementById('theme-toggle-checkbox');

    const setTheme = (theme) => {
        document.body.classList.remove('dark-mode', 'light-mode');
        document.body.classList.add(theme);
        localStorage.setItem('theme', theme);
        if (themeToggleCheckbox) {
            themeToggleCheckbox.checked = (theme === 'light-mode');
        }
    };

    setTheme(localStorage.getItem('theme') || 'dark-mode');

    if (themeToggleCheckbox) {
        themeToggleCheckbox.addEventListener('change', () => {
            setTheme(themeToggleCheckbox.checked ? 'light-mode' : 'dark-mode');
        });
    }

    // --- Product Card HTML ---
    const createProductCardHtml = (product) => {
        return `
            <div class="product-card">
                <img src="${product.image}" alt="${product.name}" width="300" height="200"
                     onerror="this.onerror=null;this.src='https://placehold.co/300x200/cccccc/333333?text=Imagen+no+disponible';">
                <h2>${product.name}</h2>
                <p>${product.description}</p>
                <p class="price">$${product.price}</p>
                <button class="add-to-cart-btn" data-product-name="${product.name}">Añadir al carrito</button>
            </div>
        `;
    };

    // --- Product Display ---
    const updateProductDisplay = () => {
        productGridContainer.innerHTML = '';

        let productsToFilter = [...allProductsData];

        if (activeFilter !== 'todos los productos') {
            productsToFilter = productsToFilter.filter(product =>
                product.category.includes(activeFilter.slice(0, -1)) || product.category === activeFilter
            );
        }

        if (currentSearchTerm) {
            const searchTermLower = currentSearchTerm.toLowerCase();
            productsToFilter = productsToFilter.filter(product =>
                product.name.toLowerCase().includes(searchTermLower) ||
                product.description.toLowerCase().includes(searchTermLower) ||
                product.category.toLowerCase().includes(searchTermLower)
            );
        }

        if (visibleCounts[activeFilter] === undefined) {
            visibleCounts[activeFilter] = initialDisplayCount;
        }

        const productsToDisplay = productsToFilter.slice(0, visibleCounts[activeFilter]);

        if (productsToDisplay.length === 0) {
            productGridContainer.innerHTML = '<p class="text-center text-xl text-gray-500 col-span-full py-10">No se encontraron productos que coincidan con su búsqueda o filtro.</p>';
            loadMoreContainer.style.display = 'none';
        } else {
            productsToDisplay.forEach(product => {
                productGridContainer.insertAdjacentHTML('beforeend', createProductCardHtml(product));
            });
            loadMoreContainer.style.display =
                productsToFilter.length > visibleCounts[activeFilter] ? 'block' : 'none';
        }
    };

    // --- Load products from API ---
    async function loadProducts() {
        try {
            const res = await fetch('/api/products');
            allProductsData = await res.json();

            filterButtons.forEach(button => {
                visibleCounts[button.textContent.toLowerCase()] = initialDisplayCount;
            });

            updateProductDisplay();
        } catch (err) {
            console.error('Error cargando productos:', err);
            productGridContainer.innerHTML = '<p class="text-center text-xl text-gray-500 col-span-full py-10">No se pudieron cargar los productos.</p>';
        }
    }

    loadProducts();

    // --- Filter Buttons ---
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            activeFilter = button.textContent.toLowerCase();
            currentSearchTerm = '';
            if (desktopSearchInput) desktopSearchInput.value = '';
            updateProductDisplay();
        });
    });

    // --- Search ---
    const performSearch = () => {
        currentSearchTerm = desktopSearchInput.value.trim();
        filterButtons.forEach(btn => btn.classList.remove('active'));
        const allBtn = Array.from(filterButtons).find(btn => btn.textContent.toLowerCase() === 'todos los productos');
        if (allBtn) allBtn.classList.add('active');
        activeFilter = 'todos los productos';
        Object.keys(visibleCounts).forEach(key => { visibleCounts[key] = initialDisplayCount; });
        updateProductDisplay();
        setTimeout(() => {
            if (productGridContainer) productGridContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    };

    if (desktopSearchInput) {
        desktopSearchInput.addEventListener('keyup', (event) => {
            if (event.key === 'Enter') performSearch();
            else if (desktopSearchInput.value.trim() === '' && currentSearchTerm !== '') performSearch();
        });
    }
    if (desktopSearchButton) desktopSearchButton.addEventListener('click', performSearch);

    // --- Load More ---
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            visibleCounts[activeFilter] += productsPerLoad;
            updateProductDisplay();
        });
    }

    // --- Shopping Cart ---
    let cart = [];

    const updateCartQuantityDisplay = () => {
        if (cartQuantitySpan) {
            cartQuantitySpan.textContent = cart.length;
            cartQuantitySpan.classList.toggle('hidden', cart.length === 0);
        }
    };

    updateCartQuantityDisplay();

    const renderCartItems = () => {
        cartItemsContainer.innerHTML = '';

        if (cart.length === 0) {
            emptyCartMessage.style.display = 'block';
            requestQuoteFromCartBtn.disabled = true;
            requestQuoteFromCartBtn.classList.add('opacity-50', 'cursor-not-allowed');
            cartTotalPriceSpan.textContent = '$0.00';
        } else {
            emptyCartMessage.style.display = 'none';
            requestQuoteFromCartBtn.disabled = false;
            requestQuoteFromCartBtn.classList.remove('opacity-50', 'cursor-not-allowed');

            let totalPrice = 0;
            const itemCounts = {};
            cart.forEach(item => { itemCounts[item.id] = (itemCounts[item.id] || 0) + 1; });

            const uniqueCartItems = Array.from(new Set(cart.map(item => item.id)))
                .map(id => allProductsData.find(product => product.id === id));

            uniqueCartItems.forEach(product => {
                const quantity = itemCounts[product.id];
                const itemPrice = parseFloat(product.price.replace(',', '')) * quantity;
                totalPrice += itemPrice;

                cartItemsContainer.insertAdjacentHTML('beforeend', `
                    <div class="cart-item" data-product-id="${product.id}">
                        <img src="${product.image}" alt="${product.name}" class="cart-item-image">
                        <div class="cart-item-details">
                            <h3>${product.name}</h3>
                            <p>Cantidad: ${quantity}</p>
                        </div>
                        <span class="cart-item-price">$${itemPrice.toFixed(2)}</span>
                        <button class="remove-from-cart-btn text-gray-400 hover:text-red-500 transition-colors duration-200 ml-2" aria-label="Eliminar ${product.name}">
                            <i class="fas fa-times-circle"></i>
                        </button>
                    </div>
                `);
            });

            cartTotalPriceSpan.textContent = `$${totalPrice.toFixed(2)}`;
        }
    };

    // Add to cart (event delegation)
    if (productGridContainer) {
        productGridContainer.addEventListener('click', (event) => {
            const clickedButton = event.target.closest('.add-to-cart-btn');
            if (clickedButton) {
                event.preventDefault();
                const productName = clickedButton.dataset.productName;
                const productToAdd = allProductsData.find(p => p.name === productName);
                if (productToAdd) {
                    cart.push(productToAdd);
                    updateCartQuantityDisplay();
                }
            }
        });
    }

    // Open cart modal
    if (cartIcon) {
        cartIcon.addEventListener('click', (event) => {
            event.preventDefault();
            renderCartItems();
            cartModal.style.display = 'flex';
            backdropOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

    // Remove from cart
    if (cartItemsContainer) {
        cartItemsContainer.addEventListener('click', (event) => {
            const removeButton = event.target.closest('.remove-from-cart-btn');
            if (removeButton) {
                const productIdToRemove = removeButton.closest('.cart-item').dataset.productId;
                const indexToRemove = cart.findIndex(item => item.id === productIdToRemove);
                if (indexToRemove > -1) {
                    cart.splice(indexToRemove, 1);
                    updateCartQuantityDisplay();
                    renderCartItems();
                }
            }
        });
    }

    // Close cart modal
    if (closeCartModalButton) {
        closeCartModalButton.addEventListener('click', () => {
            cartModal.style.display = 'none';
            backdropOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    // Request quote from cart
    if (requestQuoteFromCartBtn) {
        requestQuoteFromCartBtn.addEventListener('click', () => {
            let messageContent = "Me gustaría solicitar una cotización personalizada para los siguientes productos:\n\n";
            const itemCounts = {};
            cart.forEach(item => { itemCounts[item.id] = (itemCounts[item.id] || 0) + 1; });

            Array.from(new Set(cart.map(item => item.id)))
                .map(id => allProductsData.find(product => product.id === id))
                .forEach(product => {
                    messageContent += `- ${product.name} (Cantidad: ${itemCounts[product.id]})\n`;
                });
            messageContent += `\nTotal estimado: ${cartTotalPriceSpan.textContent}`;

            document.getElementById('modal-message').value = messageContent;
            document.getElementById('subject').value = 'Solicitud de Cotización Personalizada';

            cartModal.style.display = 'none';
            contactModal.classList.add('modal-show');
            backdropOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

    // --- Contact Modal ---
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            contactModal.classList.remove('modal-show');
            confirmationMessage.style.display = 'none';
            modalContactForm.reset();
            backdropOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    if (contactModal) {
        contactModal.addEventListener('click', (event) => {
            if (event.target === contactModal) {
                contactModal.classList.remove('modal-show');
                confirmationMessage.style.display = 'none';
                modalContactForm.reset();
                backdropOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    if (modalContactForm) {
        modalContactForm.addEventListener('submit', (event) => {
            event.preventDefault();
            modalContactForm.style.display = 'none';
            confirmationMessage.style.display = 'block';
            setTimeout(() => {
                contactModal.classList.remove('modal-show');
                confirmationMessage.style.display = 'none';
                modalContactForm.style.display = 'flex';
                modalContactForm.reset();
                backdropOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }, 3000);
        });
    }

    // Hero quote button
    const heroQuoteBtn = document.querySelector('.hero-section .quote-btn');
    if (heroQuoteBtn) {
        heroQuoteBtn.addEventListener('click', (event) => {
            event.preventDefault();
            document.getElementById('modal-message').value = '';
            if (productInfoSpan) productInfoSpan.textContent = 'sus necesidades de equipo de cocina';
            contactModal.classList.add('modal-show');
            backdropOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

    // --- Main Contact Form ---
    if (mainContactForm) {
        mainContactForm.addEventListener('submit', (event) => {
            event.preventDefault();
            mainConfirmationMessage.classList.remove('hidden');
            mainConfirmationMessage.classList.add('block');
            setTimeout(() => {
                mainConfirmationMessage.classList.remove('block');
                mainConfirmationMessage.classList.add('hidden');
                mainContactForm.reset();
            }, 5000);
        });
    }
});
