/* =========================================
   CORE CART ENGINE (Unified for RASAYAM)
   ========================================= */
const CART_KEY = 'rasayam_cart'; // Using one consistent key

function getCart() {
    try {
        const data = localStorage.getItem(CART_KEY);
        return data ? JSON.parse(data) : []; // Always return an Array
    } catch (e) {
        return [];
    }
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartUI(); 
    syncShopButtons(); 
}

/* =========================================
   ACTIONS (Add, Update, Remove)
   ========================================= */
function addToCart(id, name, price, img) {
    let cart = getCart();
    
    // 1. Find if item exists by ID
    const existingItem = cart.find(item => String(item.id) === String(id));

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        // 2. Add as a new object in the array
        cart.push({
            id: id,
            name: name,
            price: parseFloat(price),
            image: img,
            quantity: 1
        });
    }
    saveCart(cart);
}

function updateQuantity(id, change) {
    let cart = getCart();
    const item = cart.find(item => String(item.id) === String(id));

    if (item) {
        item.quantity += change;
        if (item.quantity <= 0) {
            cart = cart.filter(i => String(i.id) !== String(id));
        }
    }
    saveCart(cart);
}

/* =========================================
   UI SYNC (The Button Switcher)
   ========================================= */
function syncShopButtons() {
    const cart = getCart();
    const containers = document.querySelectorAll('.product-action-container');
    
    containers.forEach(container => {
        const id = container.getAttribute('data-id');
        const name = container.getAttribute('data-name');
        const price = container.getAttribute('data-price');
        const img = container.getAttribute('data-img');
        
        if (!id) return;

        const itemInCart = cart.find(item => String(item.id) === String(id));

        if (itemInCart) {
            // Transform button to quantity selector
            container.innerHTML = `
                <div class="qty-selector" style="display:flex; align-items:center; justify-content:center; border:1px solid #1a1a1a; padding:8px;">
                    <button onclick="updateQuantity('${id}', -1)" style="background:none; border:none; cursor:pointer; padding:0 15px;">-</button>
                    <span style="margin:0 20px; font-weight:bold;">${itemInCart.quantity}</span>
                    <button onclick="updateQuantity('${id}', 1)" style="background:none; border:none; cursor:pointer; padding:0 15px;">+</button>
                </div>`;
        } else {
            // Standard Add button
            container.innerHTML = `
                <button class="btn-gold" style="width:100%; padding:15px; background:#1a1a1a; color:white; border:none; cursor:pointer;" 
                        onclick="addToCart('${id}', '${name.replace(/'/g, "\\'")}', ${price}, '${img}')">
                    ADD TO SELECTION
                </button>`;
        }
    });
}

function updateCartUI() {
    const cart = getCart();
    
    // 1. Update Badge
    const countBadge = document.getElementById('cart-count');
    if (countBadge) {
        countBadge.innerText = cart.reduce((sum, item) => sum + item.quantity, 0);
    }

    // 2. Update Cart Page Items
    const itemsContainer = document.getElementById('cart-items');
    if (!itemsContainer) return; 

    if (cart.length === 0) {
        itemsContainer.innerHTML = `
            <div style="text-align:center; padding: 60px;">
                <p class="playfair" style="font-size: 1.2rem; color: #888;">Your boutique selection is empty.</p>
                <a href="/shop/" style="color: var(--gold); text-decoration: underline; margin-top: 20px; display: block;">Continue Shopping</a>
            </div>`;
        document.getElementById('cart-summary').style.display = 'none';
        return;
    }

    document.getElementById('cart-summary').style.display = 'block';
    itemsContainer.innerHTML = '';
    let total = 0;

    cart.forEach((item, index) => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;

        itemsContainer.innerHTML += `
            <div class="cart-item" style="display: flex; align-items: center; gap: 25px; padding-bottom: 30px; margin-bottom: 30px; border-bottom: 1px solid #eee;">
                <img src="${item.image}" style="width: 120px; height: 160px; object-fit: cover; border-radius: 2px;">
                <div style="flex: 1;">
                    <h4 class="playfair" style="font-size: 1.4rem; margin-bottom: 5px;">${item.name}</h4>
                    <p style="color: #888; font-size: 0.9rem;">Unit Price: ₹${item.price.toLocaleString('en-IN')}</p>
                    <div style="margin-top: 15px; display: flex; align-items: center; gap: 20px;">
                        <button onclick="updateQuantity('${item.id}', -1)" style="cursor:pointer; background:none; border: 1px solid #ccc; width: 30px; height: 30px;">-</button>
                        <span>${item.quantity}</span>
                        <button onclick="updateQuantity('${item.id}', 1)" style="cursor:pointer; background:none; border: 1px solid #ccc; width: 30px; height: 30px;">+</button>
                    </div>
                </div>
                <div style="text-align: right;">
                    <p style="font-weight: 700; font-size: 1.1rem;">₹${itemTotal.toLocaleString('en-IN')}</p>
                    <button onclick="removeItem(${index})" style="background:none; border:none; color: #999; cursor:pointer; margin-top: 10px; font-size: 0.8rem; text-decoration: underline;">Remove</button>
                </div>
            </div>`;
    });

    // Update Totals
    document.getElementById('cart-total').innerText = total.toLocaleString('en-IN');
    document.getElementById('cart-grand-total').innerText = total.toLocaleString('en-IN');
}

/* =========================================
   BOOTLOADER
   ========================================= */
document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();
    syncShopButtons();
});

/* =========================================
   FINAL ACTIONS (Clear, Remove, Checkout)
   ========================================= */

// 1. Clear the entire cart
function clearCart() {
    if (confirm("Are you sure you want to empty your boutique selection?")) {
        localStorage.removeItem(CART_KEY); // Use the unified key
        saveCart([]); // This clears the UI and badge instantly
    }
}

// 2. Remove a single item row
function removeItem(index) {
    let cart = getCart();
    cart.splice(index, 1); // Remove the item at that position
    saveCart(cart);
}

// 3. The WhatsApp Engine
async function initiateWhatsAppCheckout() {
    const cart = getCart();
    if (cart.length === 0) return alert("Your selection is empty!");

    let total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

    // --- NEW: Save to Database First ---
    try {
        const response = await fetch('/save-order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // Make sure you have a getCookie function
            },
            body: JSON.stringify({
                cart: cart,
                total_amount: total
            })
        });

        if (response.ok) {
            console.log("Order saved to Rasayam database.");
        }
    } catch (error) {
        console.error("Database sync failed, but proceeding to WhatsApp...", error);
    }

    // --- EXISTING: Open WhatsApp ---
    let msg = "*RASAYAM Boutique - New Order Selection*\n";
    // ... (Your existing message formatting code) ...
    
    window.open(`https://wa.me/8279710603?text=${encodeURIComponent(msg)}`, '_blank');
    
    // Optional: Clear cart after successful checkout
    // clearCart(); 
}

// Helper to get CSRF token for Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}