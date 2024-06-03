let recipes = [];
let weeklyList = [];

async function fetchRecipes() {
    try {
        const response = await fetch('recipes.json');
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        recipes = await response.json();
        displayRecipes();
    } catch (error) {
        console.error('Error fetching recipes:', error);
    }
}

function displayRecipes() {
    const recipesContainer = document.querySelector('.recipes');
    recipes.forEach((recipe, index) => {
        const recipeElement = document.createElement('div');
        recipeElement.className = 'recipe';
        recipeElement.innerHTML = `
            <img src="${recipe.hero_image_url}" alt="${recipe.title}" />
            <h3>${recipe.title}</h3>
            <button onclick="addToWeeklyList(${index})">+</button>
        `;
        recipesContainer.appendChild(recipeElement);
    });
}

function showPopup(recipe) {
    const popup = document.getElementById('recipe-popup');
    const popupContent = document.getElementById('popup-content');
    popupContent.innerHTML = `
        <h2>${recipe.title}</h2>
        <img src="${recipe.hero_image_url}" alt="${recipe.title}" />
        <h3>Ingredients</h3>
        <ul>${recipe.ingredients.map(ingredient => `<li>${ingredient.name}: ${ingredient.unit}</li>`).join('')}</ul>
        <h3>Instructions</h3>
        ${recipe.instructions.map(step => `
            <div>
                <p>${step.text}</p>
                <img src="${step.image_url}" alt="Step image" />
            </div>
        `).join('')}
    `;
    popup.style.display = 'block';
}

function closePopup() {
    document.getElementById('recipe-popup').style.display = 'none';
}

function addToWeeklyList(recipeIndex) {
    const recipe = recipes[recipeIndex];
    if (!weeklyList.some(r => r.title === recipe.title)) { // Check if recipe is already in the list
        weeklyList.push(recipe);
        console.log('Recipe added to weekly list:', recipe.title);
        updateWeeklyList();
    }
}

function updateWeeklyList() {
    const weeklyListContainer = document.getElementById('weekly-list');
    if (weeklyListContainer) {
        weeklyListContainer.innerHTML = weeklyList.map(recipe => `<li>${recipe.title}</li>`).join('');
    }
}

function goToNextPage() {
    console.log('Saving weekly list to sessionStorage:', JSON.stringify(weeklyList));
    sessionStorage.setItem('weeklyList', JSON.stringify(weeklyList));
    window.location.href = 'page2.html';
}

document.addEventListener('DOMContentLoaded', () => {
    fetchRecipes();
});
