const API = {
    initData: '',

    init() {
        const tg = window.Telegram?.WebApp;
        if (tg) {
            tg.ready();
            tg.expand();
            this.initData = tg.initData || '';
            if (tg.themeParams) {
                const root = document.documentElement;
                for (const [key, value] of Object.entries(tg.themeParams)) {
                    root.style.setProperty(`--tg-theme-${key.replace(/_/g, '-')}`, value);
                }
            }
        }
    },

    async request(method, path, body = null) {
        const opts = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-Telegram-Init-Data': this.initData,
            },
        };
        if (body) opts.body = JSON.stringify(body);

        const res = await fetch(path, opts);
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Ошибка сервера' }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        if (res.status === 204) return null;
        return res.json();
    },

    get: (path) => API.request('GET', path),
    post: (path, body) => API.request('POST', path, body),
    put: (path, body) => API.request('PUT', path, body),
    del: (path) => API.request('DELETE', path),

    // Users
    getMe: () => API.get('/api/users/me'),
    getUsers: () => API.get('/api/users'),
    updateUserRole: (id, role) => API.put(`/api/users/${id}/role`, { role }),

    // Inventory
    getIngredients: () => API.get('/api/inventory/ingredients'),
    createIngredient: (data) => API.post('/api/inventory/ingredients', data),
    updateIngredient: (id, data) => API.put(`/api/inventory/ingredients/${id}`, data),
    deleteIngredient: (id) => API.del(`/api/inventory/ingredients/${id}`),
    updateRevision: (id, quantity) => API.post(`/api/inventory/ingredients/${id}/revision`, { quantity }),
    getOrders: (resolved = false) => API.get(`/api/inventory/orders?resolved=${resolved}`),
    createOrder: (ingredientId) => API.post('/api/inventory/orders', { ingredient_id: ingredientId }),
    resolveOrder: (id) => API.post(`/api/inventory/orders/${id}/resolve`),

    // Recipes
    getRecipes: () => API.get('/api/recipes'),
    getRecipe: (id) => API.get(`/api/recipes/${id}`),
    createRecipe: (data) => API.post('/api/recipes', data),
    updateRecipe: (id, data) => API.put(`/api/recipes/${id}`, data),
    deleteRecipe: (id) => API.del(`/api/recipes/${id}`),
};
