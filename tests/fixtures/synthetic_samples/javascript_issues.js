/**
 * Synthetic JavaScript code samples with known quality issues.
 * These samples are designed to test JavaScript analyzers.
 */

// SECURITY ISSUE: Dangerous eval usage
function executeUserCode(userInput) {
    // Vulnerable: eval with user input
    return eval(userInput);
}

// SECURITY ISSUE: XSS vulnerability
function displayUserMessage(message) {
    // Vulnerable: Direct DOM manipulation without sanitization
    document.getElementById('content').innerHTML = message;
}

// SECURITY ISSUE: Hardcoded credentials
const API_CONFIG = {
    apiKey: 'sk-1234567890abcdef',
    secretKey: 'secret_key_12345',
    databasePassword: 'admin123'
};

// PERFORMANCE ISSUE: Inefficient nested loops
function findDuplicates(arr1, arr2) {
    const duplicates = [];
    for (let i = 0; i < arr1.length; i++) {
        for (let j = 0; j < arr2.length; j++) {
            if (arr1[i] === arr2[j]) {
                duplicates.push(arr1[i]);
            }
        }
    }
    return duplicates;
}

// PERFORMANCE ISSUE: Memory leak through event listeners
function setupEventListeners() {
    const buttons = document.querySelectorAll('.button');
    buttons.forEach(button => {
        // Memory leak: event listeners not removed
        button.addEventListener('click', function() {
            console.log('Button clicked');
        });
    });
}

// COMPLEXITY ISSUE: Deeply nested conditions
function processUserPermissions(user, action, resource, context) {
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
                        } else if (context && context.sharedWith) {
                            if (context.sharedWith.includes(user.id)) {
                                return true;
                            }
                        }
                    } else if (resource.type === 'folder') {
                        if (user.permissions.folders.includes('read')) {
                            return true;
                        }
                    }
                } else if (action === 'write') {
                    if (resource.owner === user.id) {
                        if (user.permissions.write) {
                            return true;
                        }
                    } else if (user.role === 'admin') {
                        return true;
                    }
                }
            }
        }
    }
    return false;
}

// DUPLICATION ISSUE: Repeated validation logic
function validateUserEmail(email) {
    if (!email) {
        return { valid: false, error: 'Email is required' };
    }
    if (!email.includes('@')) {
        return { valid: false, error: 'Invalid email format' };
    }
    if (email.length < 5) {
        return { valid: false, error: 'Email too short' };
    }
    return { valid: true };
}

function validateAdminEmail(email) {
    if (!email) {
        return { valid: false, error: 'Email is required' };
    }
    if (!email.includes('@')) {
        return { valid: false, error: 'Invalid email format' };
    }
    if (email.length < 5) {
        return { valid: false, error: 'Email too short' };
    }
    if (!email.endsWith('@company.com')) {
        return { valid: false, error: 'Must be company email' };
    }
    return { valid: true };
}

// DOCUMENTATION ISSUE: Missing JSDoc
function calculateTax(amount, rate, region) {
    let tax = amount * rate;
    if (region === 'EU') {
        tax *= 1.2;
    }
    return tax;
}

// DOCUMENTATION ISSUE: Inadequate documentation
/**
 * Process data
 */
function processData(data, options) {
    // Complex processing logic without proper documentation
    const result = data.map(item => {
        if (options.transform) {
            return transformItem(item, options.transformOptions);
        }
        return item;
    }).filter(item => {
        if (options.filter) {
            return applyFilter(item, options.filterCriteria);
        }
        return true;
    });
    
    return result;
}

// TESTING ISSUE: Function without tests
function calculateCompoundInterest(principal, rate, time, frequency) {
    return principal * Math.pow(1 + rate / frequency, frequency * time);
}

// ERROR HANDLING ISSUE: Missing error handling
function parseJSON(jsonString) {
    // No error handling for invalid JSON
    return JSON.parse(jsonString);
}

function fetchUserData(userId) {
    // No error handling for network failures
    return fetch(`/api/users/${userId}`)
        .then(response => response.json());
}

// PERFORMANCE ISSUE: Inefficient DOM manipulation
function updateUserList(users) {
    const container = document.getElementById('user-list');
    
    // Inefficient: clearing and rebuilding entire list
    container.innerHTML = '';
    
    users.forEach(user => {
        // Inefficient: creating elements one by one
        const div = document.createElement('div');
        div.className = 'user-item';
        div.innerHTML = `
            <span class="name">${user.name}</span>
            <span class="email">${user.email}</span>
        `;
        container.appendChild(div);
    });
}

// COMPLEXITY ISSUE: Function with too many responsibilities
function handleFormSubmission(formData) {
    // Validation
    const errors = [];
    if (!formData.name) errors.push('Name is required');
    if (!formData.email) errors.push('Email is required');
    if (!formData.password) errors.push('Password is required');
    
    if (errors.length > 0) {
        displayErrors(errors);
        return;
    }
    
    // Data transformation
    const processedData = {
        name: formData.name.trim().toLowerCase(),
        email: formData.email.trim().toLowerCase(),
        password: hashPassword(formData.password),
        createdAt: new Date().toISOString()
    };
    
    // API call
    fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(processedData)
    })
    .then(response => response.json())
    .then(data => {
        // Success handling
        showSuccessMessage('User created successfully');
        resetForm();
        redirectToUserList();
        
        // Analytics tracking
        trackEvent('user_created', { userId: data.id });
        
        // Email notification
        sendWelcomeEmail(data.email);
    })
    .catch(error => {
        // Error handling
        console.error('Error:', error);
        showErrorMessage('Failed to create user');
    });
}

// DUPLICATION ISSUE: Similar CRUD operations
function createUser(userData) {
    return fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
    }).then(response => {
        if (!response.ok) {
            throw new Error('Failed to create user');
        }
        return response.json();
    });
}

function createProduct(productData) {
    return fetch('/api/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(productData)
    }).then(response => {
        if (!response.ok) {
            throw new Error('Failed to create product');
        }
        return response.json();
    });
}

function createOrder(orderData) {
    return fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
    }).then(response => {
        if (!response.ok) {
            throw new Error('Failed to create order');
        }
        return response.json();
    });
}

// PERFORMANCE ISSUE: Inefficient array operations
function processLargeDataset(data) {
    let result = data;
    
    // Multiple array iterations instead of single pass
    result = result.filter(item => item.active);
    result = result.map(item => ({ ...item, processed: true }));
    result = result.sort((a, b) => a.name.localeCompare(b.name));
    result = result.slice(0, 100);
    
    return result;
}

// SECURITY ISSUE: Unsafe regular expression
function validateInput(input) {
    // Vulnerable to ReDoS (Regular Expression Denial of Service)
    const regex = /^(a+)+$/;
    return regex.test(input);
}

// MAINTAINABILITY ISSUE: Magic numbers and unclear logic
function calculatePricing(basePrice, customerType, quantity, seasonalFactor) {
    let price = basePrice;
    
    // Magic numbers without explanation
    if (customerType === 'premium') {
        price *= 0.85;
    } else if (customerType === 'gold') {
        price *= 0.9;
    }
    
    if (quantity > 10) {
        price *= 0.95;
    } else if (quantity > 50) {
        price *= 0.88;
    } else if (quantity > 100) {
        price *= 0.8;
    }
    
    price *= seasonalFactor;
    
    if (price < basePrice * 0.6) {
        price = basePrice * 0.6;
    }
    
    return price;
}

// Helper functions (stubs)
function transformItem(item, options) { return item; }
function applyFilter(item, criteria) { return true; }
function displayErrors(errors) { console.error(errors); }
function hashPassword(password) { return 'hashed_' + password; }
function showSuccessMessage(message) { console.log(message); }
function resetForm() { }
function redirectToUserList() { }
function trackEvent(event, data) { }
function sendWelcomeEmail(email) { }