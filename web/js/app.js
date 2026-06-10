const App = {
    user: null,
    currentTab: 'recipes',
    isChef: false,

    roleLabels: {
        cook: 'Повар',
        sous_chef: 'Су-шеф',
        chef: 'Шеф',
        admin: 'Админ',
    },

    tabTitles: {
        revision: 'Ревизия',
        recipes: 'ТТК',
        orders: 'К заказу',
        users: 'Управление ролями',
    },

    async init() {
        API.init();
        try {
            this.user = await API.getMe();
            this.isChef = ['sous_chef', 'chef', 'admin'].includes(this.user.role);
            this.setupUI();
            this.setupNav();
            this.setupModal();
            await this.render();
            if (this.isChef) this.updateOrdersBadge();
        } catch (e) {
            document.getElementById('content').innerHTML =
                `<div class="empty-state"><div class="empty-icon empty-icon-error"></div><p>Ошибка загрузки: ${e.message}</p></div>`;
        }
    },

    setupUI() {
        const badge = document.getElementById('user-badge');
        badge.textContent = this.roleLabels[this.user.role] || this.user.role;
        badge.className = `badge ${this.user.role}`;

        document.querySelectorAll('.chef-only').forEach(el => {
            el.classList.toggle('hidden', !this.isChef);
        });
    },

    setupNav() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;
                if (tab === this.currentTab) return;
                this.currentTab = tab;
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById('page-title').textContent = this.tabTitles[tab];
                this.render();
            });
        });
    },

    setupModal() {
        const modal = document.getElementById('modal');
        modal.querySelector('.modal-backdrop').addEventListener('click', () => this.closeModal());
        modal.querySelector('.modal-close').addEventListener('click', () => this.closeModal());
    },

    openModal(title, bodyHTML, footerHTML = '') {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = bodyHTML;
        document.getElementById('modal-footer').innerHTML = footerHTML;
        document.getElementById('modal').classList.remove('hidden');
    },

    closeModal() {
        document.getElementById('modal').classList.add('hidden');
    },

    toast(msg, type = '') {
        const el = document.getElementById('toast');
        el.textContent = msg;
        el.className = `toast ${type}`;
        el.classList.remove('hidden');
        setTimeout(() => el.classList.add('hidden'), 3000);
    },

    formatDate(dt) {
        if (!dt) return '—';
        const d = new Date(dt + (dt.includes('Z') ? '' : 'Z'));
        return d.toLocaleString('ru-RU', {
            day: '2-digit', month: '2-digit', year: '2-digit',
            hour: '2-digit', minute: '2-digit',
        });
    },

    formatTime(dt) {
        if (!dt) return '—';
        const d = new Date(dt + (dt.includes('Z') ? '' : 'Z'));
        return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    },

    assignableRoles() {
        const roles = {
            cook: [],
            sous_chef: ['cook', 'sous_chef'],
            chef: ['cook', 'sous_chef', 'chef'],
            admin: ['cook', 'sous_chef', 'chef', 'admin'],
        };
        return roles[this.user?.role] || [];
    },

    canEditUserRole(user) {
        if (user.id === this.user.id) return false;
        if (user.role === 'admin' && this.user.role !== 'admin') return false;
        return this.assignableRoles().includes(user.role);
    },

    roleOptionsHTML(selectedRole) {
        return this.assignableRoles().map(role =>
            `<option value="${role}" ${selectedRole === role ? 'selected' : ''}>${this.roleLabels[role]}</option>`
        ).join('');
    },

    async render() {
        const content = document.getElementById('content');
        content.innerHTML = '<div class="empty-state">Загрузка...</div>';

        const renderers = {
            revision: () => this.renderRevision(),
            recipes: () => this.renderRecipes(),
            orders: () => this.renderOrders(),
            users: () => this.renderUsers(),
        };

        try {
            await renderers[this.currentTab]();
        } catch (e) {
            content.innerHTML = `<div class="empty-state"><div class="empty-icon empty-icon-error"></div><p>${e.message}</p></div>`;
        }
    },

    // ─── РЕВИЗИЯ ───
    async renderRevision() {
        const ingredients = await API.getIngredients();
        const content = document.getElementById('content');

        let html = '';
        if (this.isChef) {
            html += `<button class="fab" onclick="App.showAddIngredient()">+</button>`;
        }

        if (ingredients.length === 0) {
            html += `<div class="empty-state">
                <div class="empty-icon"></div>
                <p>Нет ингредиентов</p>
                ${this.isChef ? '<p>Нажмите + чтобы добавить</p>' : ''}
            </div>`;
        } else {
            html += `<div class="search-bar"><input type="text" placeholder="Поиск..." oninput="App.filterIngredients(this.value)"></div>`;
            html += `<div class="card" id="ingredients-list">`;
            ingredients.forEach(ing => {
                const stockClass = ing.needs_order ? 'critical-stock' :
                    (ing.current_quantity !== null && ing.min_quantity > 0 && ing.current_quantity <= ing.min_quantity * 1.5) ? 'low-stock' : '';
                html += `
                    <div class="ingredient-item ${stockClass}" data-name="${ing.name.toLowerCase()}">
                        <div class="ingredient-info">
                            <div class="ingredient-name">${ing.name}</div>
                            <div class="ingredient-meta">
                                Мин: ${ing.min_quantity} ${ing.unit}
                                ${ing.current_quantity !== null ? ` | Факт: ${ing.current_quantity} ${ing.unit}` : ''}
                                ${ing.needs_order ? ' | <span class="meta-alert">Заказать</span>' : ''}
                            </div>
                        </div>
                        <div class="ingredient-qty">
                            <input type="number" step="0.1" min="0"
                                value="${ing.current_quantity ?? ''}"
                                placeholder="0"
                                onchange="App.handleRevision(${ing.id}, this.value)">
                            <span>${ing.unit}</span>
                        </div>
                        ${this.isChef ? `
                            <button class="btn btn-sm btn-outline" onclick="App.showEditIngredient(${ing.id})">Изм.</button>
                        ` : ''}
                    </div>`;
            });
            html += `</div>`;
        }

        content.innerHTML = html;
    },

    filterIngredients(query) {
        const q = query.toLowerCase();
        document.querySelectorAll('#ingredients-list .ingredient-item').forEach(el => {
            el.style.display = el.dataset.name.includes(q) ? '' : 'none';
        });
    },

    async handleRevision(id, value) {
        const qty = parseFloat(value);
        if (isNaN(qty) || qty < 0) return;
        try {
            await API.updateRevision(id, qty);
            this.toast('Количество обновлено', 'success');
            if (this.isChef) this.updateOrdersBadge();
        } catch (e) { this.toast(e.message, 'error'); }
    },

    showAddIngredient() {
        this.openModal('Добавить ингредиент', `
            <div class="form-group">
                <label>Название</label>
                <input id="ing-name" type="text" placeholder="Например: Мука">
            </div>
            <div class="form-group">
                <label>Единица измерения</label>
                <select id="ing-unit">
                    <option value="кг">кг</option>
                    <option value="г">г</option>
                    <option value="л">л</option>
                    <option value="мл">мл</option>
                    <option value="шт">шт</option>
                    <option value="уп">уп</option>
                </select>
            </div>
            <div class="form-group">
                <label>Минимальный остаток</label>
                <input id="ing-min" type="number" step="0.1" min="0" value="0">
            </div>
        `, `<button class="btn btn-primary" onclick="App.handleAddIngredient()">Добавить</button>`);
    },

    async handleAddIngredient() {
        const name = document.getElementById('ing-name').value.trim();
        const unit = document.getElementById('ing-unit').value;
        const min_quantity = parseFloat(document.getElementById('ing-min').value) || 0;
        if (!name) { this.toast('Введите название', 'error'); return; }
        try {
            await API.createIngredient({ name, unit, min_quantity });
            this.closeModal();
            this.toast('Ингредиент добавлен', 'success');
            await this.render();
        } catch (e) { this.toast(e.message, 'error'); }
    },

    async showEditIngredient(id) {
        const ingredients = await API.getIngredients();
        const ing = ingredients.find(i => i.id === id);
        if (!ing) return;

        this.openModal('Редактировать', `
            <div class="form-group">
                <label>Название</label>
                <input id="edit-ing-name" type="text" value="${ing.name}">
            </div>
            <div class="form-group">
                <label>Единица измерения</label>
                <select id="edit-ing-unit">
                    ${['кг','г','л','мл','шт','уп'].map(u =>
                        `<option value="${u}" ${u === ing.unit ? 'selected' : ''}>${u}</option>`
                    ).join('')}
                </select>
            </div>
            <div class="form-group">
                <label>Минимальный остаток</label>
                <input id="edit-ing-min" type="number" step="0.1" min="0" value="${ing.min_quantity}">
            </div>
        `, `
            <div class="btn-group">
                <button class="btn btn-danger btn-sm" onclick="App.handleDeleteIngredient(${id})">Удалить</button>
                <button class="btn btn-primary" onclick="App.handleEditIngredient(${id})">Сохранить</button>
            </div>
        `);
    },

    async handleEditIngredient(id) {
        const name = document.getElementById('edit-ing-name').value.trim();
        const unit = document.getElementById('edit-ing-unit').value;
        const min_quantity = parseFloat(document.getElementById('edit-ing-min').value);
        try {
            await API.updateIngredient(id, { name, unit, min_quantity });
            this.closeModal();
            this.toast('Сохранено', 'success');
            await this.render();
            this.updateOrdersBadge();
        } catch (e) { this.toast(e.message, 'error'); }
    },

    async handleDeleteIngredient(id) {
        if (!confirm('Удалить ингредиент?')) return;
        try {
            await API.deleteIngredient(id);
            this.closeModal();
            this.toast('Удалено', 'success');
            await this.render();
        } catch (e) { this.toast(e.message, 'error'); }
    },

    // ─── ТТК ───
    async renderRecipes() {
        const recipes = await API.getRecipes();
        const content = document.getElementById('content');

        let html = '';
        if (this.isChef) {
            html += `<button class="fab" onclick="App.showAddRecipe()">+</button>`;
        }

        if (recipes.length === 0) {
            html += `<div class="empty-state">
                <div class="empty-icon"></div>
                <p>Нет рецептов</p>
                ${this.isChef ? '<p>Нажмите + чтобы создать ТТК</p>' : ''}
            </div>`;
        } else {
            html += `<div class="search-bar"><input type="text" placeholder="Поиск блюда..." oninput="App.filterRecipes(this.value)"></div>`;
            recipes.forEach(r => {
                html += `
                    <div class="card recipe-card" data-name="${r.name.toLowerCase()}" onclick="App.showRecipe(${r.id})">
                        <div class="card-title">${r.name}</div>
                        ${r.portion_weight ? `<div class="card-subtitle">Выход: ${r.portion_weight}</div>` : ''}
                        <div class="card-subtitle">${r.ingredients.length} ингредиентов</div>
                    </div>`;
            });
        }

        content.innerHTML = html;
    },

    filterRecipes(query) {
        const q = query.toLowerCase();
        document.querySelectorAll('.recipe-card').forEach(el => {
            el.style.display = el.dataset.name.includes(q) ? '' : 'none';
        });
    },

    async showRecipe(id) {
        const recipe = await API.getRecipe(id);
        let ingHTML = recipe.ingredients.map(ri =>
            `<div class="recipe-ingredient-row">
                <span>${ri.name}</span>
                <span>${ri.quantity} ${ri.unit}</span>
            </div>`
        ).join('');

        const footer = this.isChef ? `
            <div class="btn-group">
                <button class="btn btn-danger btn-sm" onclick="App.handleDeleteRecipe(${id})">Удалить</button>
                <button class="btn btn-primary btn-sm" onclick="App.closeModal(); App.showEditRecipe(${id})">Редактировать</button>
            </div>
        ` : '';

        this.openModal(recipe.name, `
            ${recipe.description ? `<p style="margin-bottom:12px;color:var(--tg-theme-hint-color)">${recipe.description}</p>` : ''}
            ${recipe.portion_weight ? `<p><b>Выход:</b> ${recipe.portion_weight}</p>` : ''}
            <div class="recipe-ingredients">
                <div class="card-title" style="font-size:14px;margin-bottom:8px">Ингредиенты</div>
                ${ingHTML}
            </div>
            <div class="recipe-instructions">${recipe.instructions}</div>
        `, footer);
    },

    showAddRecipe() {
        this.openModal('Новая ТТК', this.recipeFormHTML(), `
            <button class="btn btn-primary" onclick="App.handleSaveRecipe()">Создать</button>
        `);
    },

    async showEditRecipe(id) {
        const recipe = await API.getRecipe(id);
        this.openModal('Редактировать ТТК', this.recipeFormHTML(recipe), `
            <button class="btn btn-primary" onclick="App.handleSaveRecipe(${id})">Сохранить</button>
        `);
    },

    recipeFormHTML(recipe = null) {
        const ings = recipe?.ingredients || [];
        return `
            <div class="form-group">
                <label>Название блюда</label>
                <input id="recipe-name" type="text" value="${recipe?.name || ''}" placeholder="Борщ">
            </div>
            <div class="form-group">
                <label>Описание</label>
                <input id="recipe-desc" type="text" value="${recipe?.description || ''}" placeholder="Краткое описание">
            </div>
            <div class="form-group">
                <label>Выход порции</label>
                <input id="recipe-portion" type="text" value="${recipe?.portion_weight || ''}" placeholder="300 г">
            </div>
            <div class="form-group">
                <label>Технология приготовления</label>
                <textarea id="recipe-instructions" placeholder="Опишите процесс приготовления...">${recipe?.instructions || ''}</textarea>
            </div>
            <div class="form-group">
                <label>Ингредиенты</label>
                <div id="recipe-ingredients-list">
                    ${ings.map((ing, i) => this.recipeIngredientRowHTML(ing, i)).join('')}
                </div>
                <button class="btn btn-outline btn-sm" style="margin-top:8px" onclick="App.addRecipeIngredientRow()">+ Ингредиент</button>
            </div>
        `;
    },

    recipeIngredientRowHTML(ing = {}, idx = 0) {
        return `
            <div class="ingredient-item" data-idx="${idx}" style="gap:6px">
                <input type="text" class="ri-name" value="${ing.name || ''}" placeholder="Название" style="flex:2;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--tg-theme-bg-color);color:inherit">
                <input type="text" class="ri-qty" value="${ing.quantity || ''}" placeholder="Кол-во" style="width:60px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--tg-theme-bg-color);color:inherit;text-align:center">
                <input type="text" class="ri-unit" value="${ing.unit || 'г'}" placeholder="ед." style="width:40px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--tg-theme-bg-color);color:inherit;text-align:center">
            </div>`;
    },

    addRecipeIngredientRow() {
        const list = document.getElementById('recipe-ingredients-list');
        const idx = list.children.length;
        list.insertAdjacentHTML('beforeend', this.recipeIngredientRowHTML({}, idx));
    },

    collectRecipeData() {
        const ingredients = [];
        document.querySelectorAll('#recipe-ingredients-list .ingredient-item').forEach(row => {
            const name = row.querySelector('.ri-name').value.trim();
            const quantity = row.querySelector('.ri-qty').value.trim();
            const unit = row.querySelector('.ri-unit').value.trim() || 'г';
            if (name && quantity) ingredients.push({ name, quantity, unit });
        });
        return {
            name: document.getElementById('recipe-name').value.trim(),
            description: document.getElementById('recipe-desc').value.trim() || null,
            portion_weight: document.getElementById('recipe-portion').value.trim() || null,
            instructions: document.getElementById('recipe-instructions').value.trim(),
            ingredients,
        };
    },

    async handleSaveRecipe(id = null) {
        const data = this.collectRecipeData();
        if (!data.name || !data.instructions) {
            this.toast('Заполните название и технологию', 'error');
            return;
        }
        try {
            if (id) {
                await API.updateRecipe(id, data);
            } else {
                await API.createRecipe(data);
            }
            this.closeModal();
            this.toast(id ? 'ТТК обновлена' : 'ТТК создана', 'success');
            await this.render();
        } catch (e) { this.toast(e.message, 'error'); }
    },

    async handleDeleteRecipe(id) {
        if (!confirm('Удалить рецепт?')) return;
        try {
            await API.deleteRecipe(id);
            this.closeModal();
            this.toast('Рецепт удалён', 'success');
            await this.render();
        } catch (e) { this.toast(e.message, 'error'); }
    },

    // ─── ЗАКАЗ ───
    async renderOrders() {
        const orders = await API.getOrders(false);
        const content = document.getElementById('content');
        let html = `<button class="fab" onclick="App.showAddOrder()">+</button>`;

        if (orders.length === 0) {
            content.innerHTML = `${html}<div class="empty-state">
                <div class="empty-icon empty-icon-success"></div>
                <p>Всё в наличии, заказывать нечего</p>
                <p>Можно добавить ингредиент вручную</p>
            </div>`;
            return;
        }

        html += `<div class="card">`;
        orders.forEach(o => {
            html += `
                <div class="ingredient-item order-item order-alert">
                    <div class="order-info">
                        <div class="ingredient-name">${o.ingredient_name}</div>
                        <div class="ingredient-meta">
                            Остаток: ${o.quantity_at_trigger} ${o.unit} (мин: ${o.min_quantity} ${o.unit})
                        </div>
                        <div class="ingredient-meta">${this.formatDate(o.created_at)}</div>
                    </div>
                    <button class="btn btn-sm btn-success" onclick="App.handleResolveOrder(${o.id})">Готово</button>
                </div>`;
        });
        html += `</div>`;
        content.innerHTML = html;
    },

    async showAddOrder() {
        const ingredients = await API.getIngredients();
        if (ingredients.length === 0) {
            this.toast('Сначала добавьте ингредиенты в ревизии', 'error');
            return;
        }

        this.openModal('Добавить в заказ', `
            <div class="form-group">
                <label>Ингредиент</label>
                <select id="order-ingredient">
                    ${ingredients.map(ing => `
                        <option value="${ing.id}">
                            ${ing.name} (${ing.unit})
                        </option>
                    `).join('')}
                </select>
            </div>
            <p class="card-subtitle">Позиция появится в заказе, даже если остаток выше минимума.</p>
        `, `<button class="btn btn-primary" onclick="App.handleAddOrder()">Добавить</button>`);
    },

    async handleAddOrder() {
        const ingredientId = Number(document.getElementById('order-ingredient').value);
        if (!ingredientId) {
            this.toast('Выберите ингредиент', 'error');
            return;
        }

        try {
            await API.createOrder(ingredientId);
            this.closeModal();
            this.toast('Добавлено в заказ', 'success');
            await this.render();
            this.updateOrdersBadge();
        } catch (e) { this.toast(e.message, 'error'); }
    },

    async handleResolveOrder(id) {
        try {
            await API.resolveOrder(id);
            this.toast('Отмечено как заказанное', 'success');
            await this.render();
            this.updateOrdersBadge();
        } catch (e) { this.toast(e.message, 'error'); }
    },

    async updateOrdersBadge() {
        try {
            const orders = await API.getOrders(false);
            const badge = document.getElementById('orders-badge');
            if (orders.length > 0) {
                badge.textContent = orders.length;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        } catch { /* ignore */ }
    },

    // ─── РОЛИ ───
    async renderUsers() {
        const users = await API.getUsers();
        const content = document.getElementById('content');

        let html = `
            <div class="card help-card">
                <div class="card-title">Роли сотрудников</div>
                <p class="card-subtitle">Сотрудник появляется здесь после /start в боте. Доступ к изменению ролей зависит от вашей роли.</p>
            </div>
        `;

        if (users.length <= 1) {
            html += `<div class="empty-state" style="padding:24px">
                <div class="empty-icon empty-icon-users"></div>
                <p>Пока только вы</p>
                <p>Когда сотрудник откроет бота — он появится здесь</p>
            </div>`;
        }

        html += `<div class="card"><div class="card-title">Сотрудники (${users.length})</div>`;
        users.forEach(u => {
            const isMe = u.id === this.user.id;
            const canEdit = this.canEditUserRole(u);
            html += `
                <div class="user-item">
                    <div>
                        <div class="ingredient-name">${u.first_name}${isMe ? ' (вы)' : ''}</div>
                        <div class="ingredient-meta">${u.username ? '@' + u.username : 'ID: ' + u.telegram_id}</div>
                    </div>
                    ${canEdit ? `
                        <select onchange="App.handleRoleChange(${u.id}, this.value)">
                            ${this.roleOptionsHTML(u.role)}
                        </select>
                    ` : `<span class="role-chip">${this.roleLabels[u.role] || u.role}</span>`}
                </div>`;
        });
        html += `</div>`;
        content.innerHTML = html;
    },

    async handleRoleChange(userId, role) {
        try {
            await API.updateUserRole(userId, role);
            this.toast('Роль обновлена', 'success');
        } catch (e) {
            this.toast(e.message, 'error');
            await this.render();
        }
    },
};

document.addEventListener('DOMContentLoaded', () => App.init());
