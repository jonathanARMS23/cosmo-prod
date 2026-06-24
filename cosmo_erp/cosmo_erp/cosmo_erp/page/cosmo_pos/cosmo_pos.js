/* ============================================================
   Cosmo POS — Page Frappe/ERPNext v15
   Boutique cosmétique — interface caisse simplifiée
   ============================================================ */

// ── Constante CSS ─────────────────────────────────────────────────────────────
const COSMO_POS_CSS = `
/* ── Layout global ── */
.cosmo-pos-container { display: flex; flex-direction: column; height: calc(100vh - 60px); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8f9fa; }

/* ── Header ── */
.cosmo-pos-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; background: #fff; border-bottom: 2px solid #e91e8c; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.cosmo-boutique-name { font-size: 1.2em; font-weight: 700; color: #e91e8c; margin-right: 12px; }
.cosmo-datetime { color: #666; font-size: 0.9em; }
.cosmo-cashier { font-size: 0.9em; color: #444; }
.cosmo-daily-summary { font-size: 0.85em; color: #888; margin-left: 16px; }

/* ── Body ── */
.cosmo-pos-body { display: flex; flex: 1; overflow: hidden; gap: 0; }

/* ── Catalogue ── */
.cosmo-pos-catalog { flex: 7; display: flex; flex-direction: column; overflow: hidden; padding: 12px; background: #f8f9fa; }
.cosmo-catalog-filters { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.cosmo-catalog-filters .form-control { border-radius: 20px; padding-left: 16px; }
.cosmo-category-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.cosmo-cat-btn { padding: 4px 14px; border: 1px solid #e91e8c; border-radius: 20px; background: #fff; color: #e91e8c; cursor: pointer; font-size: 0.85em; transition: all .2s; }
.cosmo-cat-btn.active, .cosmo-cat-btn:hover { background: #e91e8c; color: #fff; }

/* ── Grille produits ── */
.cosmo-product-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; overflow-y: auto; flex: 1; padding-right: 4px; }
@media (max-width: 1200px) { .cosmo-product-grid { grid-template-columns: repeat(3, 1fr); } }
.cosmo-product-card { background: #fff; border: 1.5px solid #eee; border-radius: 10px; padding: 8px; cursor: pointer; transition: box-shadow .2s, border-color .2s; display: flex; flex-direction: column; }
.cosmo-product-card:hover { box-shadow: 0 4px 16px rgba(233,30,140,.18); border-color: #e91e8c; }
.cosmo-card-disabled { opacity: .5; cursor: not-allowed; }
.cosmo-product-img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 6px; margin-bottom: 6px; }
.cosmo-product-img-placeholder { width: 100%; aspect-ratio: 1; background: #fce4ec; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 2em; margin-bottom: 6px; }
.cosmo-product-info { display: flex; flex-direction: column; gap: 3px; }
.cosmo-brand { color: #999; font-size: 0.72em; text-transform: uppercase; }
.cosmo-product-name { font-size: 0.82em; font-weight: 600; color: #333; line-height: 1.2; }
.cosmo-product-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
.cosmo-price { font-weight: 700; color: #e91e8c; font-size: 0.88em; }
.cosmo-stock-badge { font-size: 0.72em; padding: 2px 7px; border-radius: 10px; }
.cosmo-stock-ok { background: #e8f5e9; color: #388e3c; }
.cosmo-stock-low { background: #fff8e1; color: #f57c00; }
.cosmo-stock-out { background: #ffebee; color: #c62828; }

/* ── Panier ── */
.cosmo-pos-cart { flex: 3; display: flex; flex-direction: column; background: #fff; border-left: 1px solid #eee; overflow: hidden; }
.cosmo-cart-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #f0f0f0; }
.cosmo-cart-header h5 { margin: 0; font-size: 1em; font-weight: 700; }
.cosmo-cart-items { flex: 1; overflow-y: auto; padding: 8px 12px; }
.cosmo-cart-empty { text-align: center; color: #bbb; padding: 40px 0; font-size: 0.9em; }
.cosmo-cart-item { padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
.cosmo-cart-item-name { font-size: 0.85em; font-weight: 600; color: #333; margin-bottom: 4px; }
.cosmo-cart-item-controls { display: flex; align-items: center; gap: 8px; }
.cosmo-qty-btn { width: 24px; height: 24px; border-radius: 50%; border: 1.5px solid #e91e8c; background: #fff; color: #e91e8c; font-size: 1em; cursor: pointer; display: flex; align-items: center; justify-content: center; line-height: 1; }
.cosmo-qty-btn:hover { background: #e91e8c; color: #fff; }
.cosmo-qty { font-weight: 700; min-width: 20px; text-align: center; }
.cosmo-item-total { margin-left: auto; font-weight: 700; color: #333; font-size: 0.88em; }
.cosmo-item-rate { color: #aaa; font-size: 0.75em; }

/* ── Footer panier ── */
.cosmo-cart-footer { padding: 12px 16px; border-top: 1px solid #f0f0f0; display: flex; flex-direction: column; gap: 10px; }
.cosmo-cart-totals { display: flex; flex-direction: column; gap: 4px; }
.cosmo-total-row { display: flex; justify-content: space-between; font-size: 0.88em; color: #444; }
.cosmo-grand-total { font-size: 1em; border-top: 1.5px solid #eee; padding-top: 6px; margin-top: 2px; }
.cosmo-discount-row { color: #e53935; }

/* ── Modes paiement ── */
.cosmo-payment-modes label { font-size: 0.8em; color: #888; margin-bottom: 4px; display: block; }
.cosmo-payment-btns { display: flex; gap: 6px; }
.cosmo-payment-btn { flex: 1; padding: 6px 4px; border: 1.5px solid #ddd; border-radius: 8px; background: #fff; font-size: 0.78em; cursor: pointer; text-align: center; transition: all .2s; }
.cosmo-payment-btn.active { border-color: #e91e8c; background: #fce4ec; color: #e91e8c; font-weight: 700; }

/* ── Remise ── */
.cosmo-discount-section { display: flex; flex-direction: column; gap: 6px; }
.cosmo-discount-input { display: flex; align-items: center; gap: 8px; }
.cosmo-discount-input span { color: #999; font-size: 0.8em; }

/* ── Bouton valider ── */
.cosmo-validate-btn { width: 100%; padding: 14px; font-size: 1em; background: #e91e8c; border: none; color: #fff; border-radius: 10px; font-weight: 700; transition: background .2s, opacity .2s; }
.cosmo-validate-btn:hover:not(:disabled) { background: #c2185b; }
.cosmo-validate-btn:disabled { opacity: .45; cursor: not-allowed; }

/* ── Utilitaires ── */
.cosmo-loading, .cosmo-error, .cosmo-empty { text-align: center; color: #bbb; padding: 40px 0; grid-column: 1/-1; }
.cosmo-error { color: #e53935; }
`;

// ── Constante HTML ─────────────────────────────────────────────────────────────
const COSMO_POS_HTML = `
<div class="cosmo-pos-container">
  <!-- HEADER -->
  <div class="cosmo-pos-header">
    <div class="cosmo-pos-header-left">
      <span class="cosmo-boutique-name">Cosmo Boutique</span>
      <span class="cosmo-datetime" id="cosmo-datetime"></span>
    </div>
    <div class="cosmo-pos-header-center">
      <span class="cosmo-cashier">
        Caissiere : <strong id="cosmo-cashier-name"></strong>
      </span>
      <span class="cosmo-daily-summary" id="cosmo-daily-summary"></span>
    </div>
    <div class="cosmo-pos-header-right">
      <button class="btn btn-default btn-sm" id="cosmo-close-register">
        Cloture de caisse
      </button>
    </div>
  </div>

  <!-- BODY -->
  <div class="cosmo-pos-body">
    <!-- GAUCHE : catalogue produits (70%) -->
    <div class="cosmo-pos-catalog">
      <!-- Barre de recherche + filtres categorie -->
      <div class="cosmo-catalog-filters">
        <input type="search" class="form-control" id="cosmo-search"
               placeholder="Rechercher un produit...">
        <div class="cosmo-category-tabs" id="cosmo-category-tabs">
          <button class="cosmo-cat-btn active" data-category="">Tous</button>
        </div>
      </div>
      <!-- Grille produits -->
      <div class="cosmo-product-grid" id="cosmo-product-grid">
        <div class="cosmo-loading">Chargement des produits...</div>
      </div>
    </div>

    <!-- DROITE : panier (30%) -->
    <div class="cosmo-pos-cart">
      <div class="cosmo-cart-header">
        <h5>Panier</h5>
        <button class="btn btn-xs btn-danger" id="cosmo-clear-cart">Vider</button>
      </div>
      <div class="cosmo-cart-items" id="cosmo-cart-items">
        <div class="cosmo-cart-empty">Panier vide</div>
      </div>
      <div class="cosmo-cart-footer">
        <div class="cosmo-cart-totals">
          <div class="cosmo-total-row">
            <span>Sous-total</span>
            <span id="cosmo-subtotal">0 Ar</span>
          </div>
          <div class="cosmo-total-row cosmo-discount-row" id="cosmo-discount-row" style="display:none">
            <span>Remise</span>
            <span id="cosmo-discount-display" class="text-danger">- 0 Ar</span>
          </div>
          <div class="cosmo-total-row cosmo-grand-total">
            <span><strong>TOTAL</strong></span>
            <span id="cosmo-grand-total"><strong>0 Ar</strong></span>
          </div>
        </div>
        <!-- Mode paiement -->
        <div class="cosmo-payment-modes">
          <label>Mode de paiement :</label>
          <div class="cosmo-payment-btns">
            <button class="cosmo-payment-btn active" data-mode="Espèces">Espèces</button>
            <button class="cosmo-payment-btn" data-mode="Carte">Carte</button>
            <button class="cosmo-payment-btn" data-mode="Mobile Money">Mobile Money</button>
          </div>
        </div>
        <!-- Remise -->
        <div class="cosmo-discount-section">
          <button class="btn btn-xs btn-default" id="cosmo-toggle-discount">
            + Ajouter une remise
          </button>
          <div id="cosmo-discount-input" style="display:none" class="cosmo-discount-input">
            <input type="number" id="cosmo-discount-pct" placeholder="% remise" min="0" max="100" class="form-control form-control-sm">
            <span>ou</span>
            <input type="number" id="cosmo-discount-amt" placeholder="Montant fixe" min="0" class="form-control form-control-sm">
          </div>
        </div>
        <!-- Bouton valider -->
        <button class="btn btn-primary btn-lg cosmo-validate-btn" id="cosmo-validate-btn" disabled>
          Valider et Imprimer
        </button>
      </div>
    </div>
  </div>
</div>
`;

// ── Class principale ───────────────────────────────────────────────────────────
class CosmoPOS {
    constructor(wrapper) {
        this.wrapper = wrapper;
        this.cart = [];           // [{item_code, item_name, qty, rate, stock_qty}]
        this.products = [];       // cache des produits charges
        this.payment_mode = 'Espèces';
        this.discount_percent = 0;
        this.discount_amount = 0;
        this.current_category = '';
        this.is_processing = false;

        this._render();
        this._bind_events();
        this._load_products();
        this._start_clock();
        this._load_daily_summary();
    }

    // ── Rendu ──────────────────────────────────────────────────────────────────
    _render() {
        // Injecte le HTML dans le wrapper Frappe
        this.wrapper.innerHTML = `<style>${COSMO_POS_CSS}</style>${COSMO_POS_HTML}`;
        // Affiche le nom de la caissiere
        const el = document.getElementById('cosmo-cashier-name');
        if (el) el.textContent = frappe.session.user_fullname || frappe.session.user;
    }

    // ── Chargement des produits ────────────────────────────────────────────────
    _load_products(category, search) {
        category = category || '';
        search = search || '';
        const grid = document.getElementById('cosmo-product-grid');
        if (grid) grid.innerHTML = '<div class="cosmo-loading">Chargement...</div>';

        frappe.call({
            method: 'cosmo_erp.cosmo_erp.page.cosmo_pos.cosmo_pos.get_items_with_stock',
            args: { category: category || null, search: search || null },
            callback: (r) => {
                this.products = r.message || [];
                this._render_product_grid(this.products);
                if (!category && !search) {
                    this._load_categories();
                }
            },
            error: () => {
                const g = document.getElementById('cosmo-product-grid');
                if (g) g.innerHTML = '<div class="cosmo-error">Erreur chargement produits</div>';
            }
        });
    }

    _load_categories() {
        frappe.call({
            method: 'cosmo_erp.cosmo_erp.page.cosmo_pos.cosmo_pos.get_item_categories',
            callback: (r) => {
                const categories = r.message || [];
                const tabsEl = document.getElementById('cosmo-category-tabs');
                if (!tabsEl) return;
                categories.forEach(cat => {
                    const btn = document.createElement('button');
                    btn.className = 'cosmo-cat-btn';
                    btn.dataset.category = cat;
                    btn.textContent = cat;
                    tabsEl.appendChild(btn);
                });
            }
        });
    }

    _render_product_grid(products) {
        const grid = document.getElementById('cosmo-product-grid');
        if (!grid) return;
        if (!products.length) {
            grid.innerHTML = '<div class="cosmo-empty">Aucun produit trouve</div>';
            return;
        }
        grid.innerHTML = products.map(p => this._product_card_html(p)).join('');
    }

    _product_card_html(p) {
        const stockClass = p.stock_qty <= 0
            ? 'cosmo-stock-out'
            : (p.cosmo_reorder_level && p.stock_qty <= p.cosmo_reorder_level
                ? 'cosmo-stock-low'
                : 'cosmo-stock-ok');
        const stockLabel = p.stock_qty <= 0
            ? 'Rupture'
            : (p.cosmo_reorder_level && p.stock_qty <= p.cosmo_reorder_level
                ? `⚠ ${p.stock_qty}`
                : `${p.stock_qty}`);
        const img = p.image
            ? `<img src="${p.image}" class="cosmo-product-img" alt="${p.item_name}" onerror="this.src='/assets/cosmo_erp/images/placeholder.png'">`
            : `<div class="cosmo-product-img-placeholder">🧴</div>`;
        const brandLabel = p.cosmo_brand
            ? `<small class="cosmo-brand">${p.cosmo_brand}</small>`
            : '';
        return `
            <div class="cosmo-product-card ${p.stock_qty <= 0 ? 'cosmo-card-disabled' : ''}"
                 data-item="${p.item_code}"
                 data-name="${p.item_name.replace(/"/g, '&quot;')}"
                 data-rate="${p.price}"
                 data-stock="${p.stock_qty}"
                 title="${p.item_name}">
                ${img}
                <div class="cosmo-product-info">
                    ${brandLabel}
                    <div class="cosmo-product-name">${p.item_name}</div>
                    <div class="cosmo-product-footer">
                        <span class="cosmo-price">${this._format_ariary(p.price)}</span>
                        <span class="cosmo-stock-badge ${stockClass}">${stockLabel}</span>
                    </div>
                </div>
            </div>`;
    }

    // ── Panier ─────────────────────────────────────────────────────────────────
    _add_to_cart(item_code, item_name, rate, stock_qty) {
        stock_qty = parseFloat(stock_qty);
        rate = parseFloat(rate);
        if (stock_qty <= 0) {
            frappe.show_alert({ message: `${item_name} est en rupture de stock`, indicator: 'red' }, 3);
            return;
        }
        const existing = this.cart.find(i => i.item_code === item_code);
        if (existing) {
            if (existing.qty >= stock_qty) {
                frappe.show_alert({ message: `Stock maximum atteint (${stock_qty})`, indicator: 'orange' }, 3);
                return;
            }
            existing.qty++;
        } else {
            this.cart.push({ item_code, item_name, qty: 1, rate, stock_qty });
        }
        this._render_cart();
    }

    _update_qty(item_code, delta) {
        const idx = this.cart.findIndex(i => i.item_code === item_code);
        if (idx < 0) return;
        this.cart[idx].qty += delta;
        if (this.cart[idx].qty <= 0) {
            this.cart.splice(idx, 1);
        }
        this._render_cart();
    }

    _clear_cart() {
        this.cart = [];
        this.discount_percent = 0;
        this.discount_amount = 0;
        const pct = document.getElementById('cosmo-discount-pct');
        const amt = document.getElementById('cosmo-discount-amt');
        if (pct) pct.value = '';
        if (amt) amt.value = '';
        this._render_cart();
    }

    _render_cart() {
        const cartEl = document.getElementById('cosmo-cart-items');
        const validateBtn = document.getElementById('cosmo-validate-btn');
        if (!cartEl) return;

        if (!this.cart.length) {
            cartEl.innerHTML = '<div class="cosmo-cart-empty">Panier vide</div>';
            if (validateBtn) validateBtn.disabled = true;
            this._update_totals(0);
            return;
        }

        cartEl.innerHTML = this.cart.map(item => `
            <div class="cosmo-cart-item" data-item="${item.item_code}">
                <div class="cosmo-cart-item-name">${item.item_name}</div>
                <div class="cosmo-cart-item-controls">
                    <button class="cosmo-qty-btn" data-item="${item.item_code}" data-delta="-1">&#x2212;</button>
                    <span class="cosmo-qty">${item.qty}</span>
                    <button class="cosmo-qty-btn" data-item="${item.item_code}" data-delta="1">+</button>
                    <span class="cosmo-item-total">${this._format_ariary(item.qty * item.rate)}</span>
                </div>
                <small class="cosmo-item-rate">${this._format_ariary(item.rate)} / u.</small>
            </div>`).join('');

        if (validateBtn) validateBtn.disabled = false;

        // Rebind qty buttons
        cartEl.querySelectorAll('.cosmo-qty-btn').forEach(btn => {
            btn.addEventListener('click', () => this._update_qty(btn.dataset.item, parseInt(btn.dataset.delta)));
        });

        // Calcul des totaux
        const subtotal = this.cart.reduce((sum, i) => sum + i.qty * i.rate, 0);
        this._update_totals(subtotal);
    }

    _update_totals(subtotal) {
        const discountByPct = subtotal * (this.discount_percent / 100);
        const discount = Math.max(this.discount_amount, discountByPct);
        const grandTotal = Math.max(subtotal - discount, 0);

        const subtotalEl = document.getElementById('cosmo-subtotal');
        const grandTotalEl = document.getElementById('cosmo-grand-total');
        const discountRow = document.getElementById('cosmo-discount-row');
        const discountDisplay = document.getElementById('cosmo-discount-display');

        if (subtotalEl) subtotalEl.textContent = this._format_ariary(subtotal);
        if (grandTotalEl) grandTotalEl.innerHTML = `<strong>${this._format_ariary(grandTotal)}</strong>`;

        if (discountRow) {
            if (discount > 0) {
                discountRow.style.display = 'flex';
                if (discountDisplay) discountDisplay.textContent = `- ${this._format_ariary(discount)}`;
            } else {
                discountRow.style.display = 'none';
            }
        }
    }

    // ── Validation / Vente ─────────────────────────────────────────────────────
    _validate_sale() {
        if (!this.cart.length || this.is_processing) return;

        this.is_processing = true;
        const btn = document.getElementById('cosmo-validate-btn');
        if (btn) {
            btn.textContent = 'Traitement...';
            btn.disabled = true;
        }

        frappe.call({
            method: 'cosmo_erp.cosmo_erp.page.cosmo_pos.cosmo_pos.create_sale',
            args: {
                items: JSON.stringify(this.cart.map(i => ({
                    item_code: i.item_code,
                    qty: i.qty,
                    rate: i.rate,
                }))),
                payment_mode: this.payment_mode,
                discount_amount: this.discount_amount,
                discount_percent: this.discount_percent,
            },
            callback: (r) => {
                if (r.message) {
                    const { invoice_name, grand_total, print_url } = r.message;
                    frappe.show_alert({
                        message: `Facture ${invoice_name} creee — ${this._format_ariary(grand_total)}`,
                        indicator: 'green'
                    }, 5);
                    // Ouverture impression dans un nouvel onglet
                    window.open(print_url, '_blank');
                    this._clear_cart();
                    this._load_daily_summary();
                }
            },
            error: (err) => {
                frappe.show_alert({
                    message: (err && err.message) ? err.message : 'Erreur lors de la vente',
                    indicator: 'red'
                }, 5);
            },
            always: () => {
                this.is_processing = false;
                const b = document.getElementById('cosmo-validate-btn');
                if (b) {
                    b.textContent = 'Valider et Imprimer';
                    b.disabled = !this.cart.length;
                }
            }
        });
    }

    // ── Summary & Clock ────────────────────────────────────────────────────────
    _load_daily_summary() {
        frappe.call({
            method: 'cosmo_erp.cosmo_erp.page.cosmo_pos.cosmo_pos.get_daily_summary',
            callback: (r) => {
                if (r.message) {
                    const { revenue, transaction_count } = r.message;
                    const el = document.getElementById('cosmo-daily-summary');
                    if (el) {
                        el.textContent = `Aujourd'hui : ${this._format_ariary(revenue)} · ${transaction_count} vente(s)`;
                    }
                }
            }
        });
    }

    _start_clock() {
        const update = () => {
            const now = new Date();
            const el = document.getElementById('cosmo-datetime');
            if (el) el.textContent = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
        };
        update();
        this._clock_interval = setInterval(update, 30000);
    }

    // ── Event binding ──────────────────────────────────────────────────────────
    _bind_events() {
        // Clic sur une carte produit (delegation)
        this.wrapper.addEventListener('click', (e) => {
            const card = e.target.closest('.cosmo-product-card');
            if (card && !card.classList.contains('cosmo-card-disabled')) {
                this._add_to_cart(
                    card.dataset.item,
                    card.dataset.name,
                    card.dataset.rate,
                    card.dataset.stock,
                );
            }
        });

        // Filtres categorie (delegation)
        const tabsEl = document.getElementById('cosmo-category-tabs');
        if (tabsEl) {
            tabsEl.addEventListener('click', (e) => {
                const btn = e.target.closest('.cosmo-cat-btn');
                if (!btn) return;
                document.querySelectorAll('.cosmo-cat-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.current_category = btn.dataset.category;
                const searchEl = document.getElementById('cosmo-search');
                this._load_products(this.current_category, searchEl ? searchEl.value : '');
            });
        }

        // Recherche (debounce 300ms)
        let searchTimeout;
        const searchEl = document.getElementById('cosmo-search');
        if (searchEl) {
            searchEl.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this._load_products(this.current_category, e.target.value.trim());
                }, 300);
            });
        }

        // Vider le panier
        const clearBtn = document.getElementById('cosmo-clear-cart');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (this.cart.length) {
                    frappe.confirm('Vider le panier ?', () => this._clear_cart());
                }
            });
        }

        // Mode paiement (delegation)
        this.wrapper.addEventListener('click', (e) => {
            const btn = e.target.closest('.cosmo-payment-btn');
            if (!btn) return;
            document.querySelectorAll('.cosmo-payment-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            this.payment_mode = btn.dataset.mode;
        });

        // Remise toggle
        const toggleDiscount = document.getElementById('cosmo-toggle-discount');
        if (toggleDiscount) {
            toggleDiscount.addEventListener('click', () => {
                const el = document.getElementById('cosmo-discount-input');
                if (el) el.style.display = el.style.display === 'none' ? 'flex' : 'none';
            });
        }

        // Remise en pourcentage
        const discountPct = document.getElementById('cosmo-discount-pct');
        if (discountPct) {
            discountPct.addEventListener('input', (e) => {
                this.discount_percent = parseFloat(e.target.value) || 0;
                this.discount_amount = 0;
                const amtEl = document.getElementById('cosmo-discount-amt');
                if (amtEl) amtEl.value = '';
                const subtotal = this.cart.reduce((s, i) => s + i.qty * i.rate, 0);
                this._update_totals(subtotal);
            });
        }

        // Remise en montant fixe
        const discountAmt = document.getElementById('cosmo-discount-amt');
        if (discountAmt) {
            discountAmt.addEventListener('input', (e) => {
                this.discount_amount = parseFloat(e.target.value) || 0;
                this.discount_percent = 0;
                const pctEl = document.getElementById('cosmo-discount-pct');
                if (pctEl) pctEl.value = '';
                const subtotal = this.cart.reduce((s, i) => s + i.qty * i.rate, 0);
                this._update_totals(subtotal);
            });
        }

        // Valider vente
        const validateBtn = document.getElementById('cosmo-validate-btn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => this._validate_sale());
        }

        // Cloture de caisse
        const closeBtn = document.getElementById('cosmo-close-register');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                frappe.call({
                    method: 'cosmo_erp.cosmo_erp.page.cosmo_pos.cosmo_pos.close_register',
                    callback: (r) => {
                        if (r.message) {
                            const { revenue, transaction_count, avg_basket } = r.message;
                            frappe.msgprint({
                                title: 'Cloture de caisse',
                                message: `
                                    <table class="table table-bordered">
                                      <tr><td>CA du jour</td><td><strong>${this._format_ariary(revenue)}</strong></td></tr>
                                      <tr><td>Transactions</td><td>${transaction_count}</td></tr>
                                      <tr><td>Panier moyen</td><td>${this._format_ariary(avg_basket)}</td></tr>
                                    </table>`,
                                indicator: 'green'
                            });
                        }
                    }
                });
            });
        }
    }

    // ── Utilitaires ────────────────────────────────────────────────────────────
    _format_ariary(amount) {
        return new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount || 0) + ' Ar';
    }
}

// ── Point d'entrée Frappe ─────────────────────────────────────────────────────
frappe.pages['cosmo-pos'].on_page_load = function(wrapper) {
    frappe.cosmo_pos = new CosmoPOS(wrapper);
};

frappe.pages['cosmo-pos'].on_page_hide = function() {
    if (frappe.cosmo_pos && frappe.cosmo_pos._clock_interval) {
        clearInterval(frappe.cosmo_pos._clock_interval);
    }
};
