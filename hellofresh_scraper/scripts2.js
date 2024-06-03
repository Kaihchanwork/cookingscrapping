function displaySelectedRecipes() {
    const selectedRecipesContainer = document.getElementById('selected-recipes');
    const shoppingListContainer = document.getElementById('shopping-list');
    const savedWeeklyList = sessionStorage.getItem('weeklyList');

    if (savedWeeklyList) {
        const weeklyList = JSON.parse(savedWeeklyList);
        console.log('Retrieved weekly list from sessionStorage:', weeklyList);

        const ingredientsMap = new Map();

        weeklyList.forEach(recipe => {
            const recipeElement = document.createElement('li');
            recipeElement.innerHTML = `
                <img src="${recipe.hero_image_url}" alt="${recipe.title}" style="width: 100px; height: auto; margin-right: 10px;">
                ${recipe.title}
            `;
            selectedRecipesContainer.appendChild(recipeElement);

            recipe.ingredients.forEach(ingredient => {
                const name = ingredient.name;
                const unit = ingredient.unit;
                const [quantity, unitType] = parseUnit(unit);

                if (ingredientsMap.has(name)) {
                    const currentUnit = ingredientsMap.get(name);
                    const newQuantity = currentUnit.quantity + quantity;
                    ingredientsMap.set(name, { quantity: newQuantity, unitType });
                } else {
                    ingredientsMap.set(name, { quantity, unitType });
                }
            });
        });

        ingredientsMap.forEach((value, name) => {
            const ingredientElement = document.createElement('li');
            ingredientElement.textContent = `${name}: ${value.quantity} ${value.unitType}`;
            shoppingListContainer.appendChild(ingredientElement);
        });
    } else {
        console.log('No weekly list found in sessionStorage');
    }
}

function parseUnit(unit) {
    const parts = unit.split(' ');
    const quantity = parseFloat(parts[0]);
    const unitType = parts.slice(1).join(' ');
    return [quantity, unitType];
}

document.addEventListener('DOMContentLoaded', () => {
    displaySelectedRecipes();
});
