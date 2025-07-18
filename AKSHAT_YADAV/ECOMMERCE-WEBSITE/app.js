const API_BASE = 'http://43.205.110.71:8000';

let categories = [];
let items = [];
let itemsByCategory = {};

const loadingDiv = document.getElementById('loading');
const itemsGrid = document.getElementById('items-grid');
const categoryTabs = document.getElementById('category-tabs');

function getRandomImage() {
  return `https://source.unsplash.com/collection/190727/200x200?sig=${Math.floor(Math.random() * 10000)}`;
}

async function fetchCategories() {
  const response = await fetch(`${API_BASE}/categories`);
  return response.json();
}

async function fetchAllItems() {
  const all = [];
  let page = 1;
  const size = 1000;

  while (true) {
    const res = await fetch(`${API_BASE}/items?page=${page}&size=${size}`);
    const data = await res.json();
    const batch = Array.isArray(data) ? data : data.items;
    if (!batch || batch.length === 0) break;
    all.push(...batch);
    if (batch.length < size) break;
    page++;
  }

  return all;
}

function renderCategoryTabs() {
  categoryTabs.innerHTML = '';

  const allBtn = document.createElement('button');
  allBtn.textContent = 'All';
  allBtn.classList.add('active');
  allBtn.onclick = () => renderItems('all');
  categoryTabs.appendChild(allBtn);

  categories.forEach(cat => {
    const name = cat.name || cat.category || cat.title;
    const btn = document.createElement('button');
    btn.textContent = name;
    btn.onclick = () => renderItems(name);
    categoryTabs.appendChild(btn);
  });
}

function renderItems(category) {
  Array.from(categoryTabs.children).forEach(btn => {
    btn.classList.toggle('active', btn.textContent === category);
  });

  itemsGrid.innerHTML = '';
  const list = category === 'all' ? items : (itemsByCategory[category] || []);

  list.forEach(item => {
    const card = document.createElement('div');
    card.className = 'item-card';
    card.innerHTML = `
      <img src="${getRandomImage()}" alt="item image">
      <h3>${item.name || item.title}</h3>
      <div class="price">₹${item.price}</div>
    `;
    itemsGrid.appendChild(card);
  });
}

async function main() {
  loadingDiv.classList.remove('hidden');
  itemsGrid.classList.add('hidden');

  const [cats, allItems] = await Promise.all([
    fetchCategories(),
    fetchAllItems()
  ]);

  categories = cats;
  items = allItems;

  itemsByCategory = {};
  items.forEach(item => {
    const cat = item.category?.name || item.category || 'Uncategorized';
    if (!itemsByCategory[cat]) itemsByCategory[cat] = [];
    itemsByCategory[cat].push(item);
  });

  renderCategoryTabs();
  renderItems('all');

  loadingDiv.classList.add('hidden');
  itemsGrid.classList.remove('hidden');
}

main();
