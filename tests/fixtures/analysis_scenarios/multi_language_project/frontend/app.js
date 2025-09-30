/**
 * Frontend JavaScript application with intentional quality issues for testing.
 */

// Security issue: hardcoded API key
const API_KEY = 'sk-1234567890abcdef';
const API_BASE_URL = 'https://api.example.com';

// Performance issue: inefficient DOM manipulation
function updateUserList(users) {
    const container = document.getElementById('user-list');
    container.innerHTML = ''; // Clearing entire container
    
    users.forEach(user => {
        // Creating elements one by one (inefficient)
        const div = document.createElement('div');
        div.className = 'user-item';
        div.innerHTML = `<span>${user.name}</span><span>${user.email}</span>`;
        container.appendChild(div);
    });
}

// Security issue: XSS vulnerability
function displayMessage(message) {
    document.getElementById('message').innerHTML = message; // Direct HTML injection
}

// Performance issue: nested loops
function findCommonElements(arr1, arr2) {
    const common = [];
    for (let i = 0; i < arr1.length; i++) {
        for (let j = 0; j < arr2.length; j++) {
            if (arr1[i] === arr2[j]) {
                common.push(arr1[i]);
            }
        }
    }
    return common;
}

// Complexity issue: deeply nested conditions
function checkUserPermissions(user, action, resource) {
    if (user) {
        if (user.isActive) {
            if (user.permissions) {
                if (action === 'read') {
                    if (resource.type === 'document') {
                        if (resource.owner === user.id) {
                            return true;
                        } else if (resource.isPublic) {
                            return true;
                        } else if (user.role === 'admin') {
                            return true;
                        }
                    }
                }
            }
        }
    }
    return false;
}

// Error handling issue: no error handling
function fetchUserData(userId) {
    return fetch(`${API_BASE_URL}/users/${userId}`)
        .then(response => response.json()); // No error handling
}

// Documentation issue: missing JSDoc
function calculateTotal(items, taxRate, discount) {
    let total = 0;
    items.forEach(item => {
        total += item.price * item.quantity;
    });
    
    if (discount > 0) {
        total -= discount;
    }
    
    total += total * taxRate;
    return total;
}

// Duplication issue: similar validation functions
function validateEmail(email) {
    if (!email) return false;
    if (!email.includes('@')) return false;
    if (email.length < 5) return false;
    return true;
}

function validateAdminEmail(email) {
    if (!email) return false;
    if (!email.includes('@')) return false;
    if (email.length < 5) return false;
    if (!email.endsWith('@company.com')) return false;
    return true;
}

// Memory leak: event listeners not removed
function setupEventListeners() {
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            console.log('Button clicked');
        });
    });
}

// Security issue: eval usage
function executeUserScript(script) {
    return eval(script); // Dangerous eval usage
}