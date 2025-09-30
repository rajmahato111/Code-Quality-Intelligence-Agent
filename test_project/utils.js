function validateInput(value) {
    if (typeof value !== 'number') {
        throw new Error('Input must be a number');
    }
    return true;
}

class MathHelper {
    static multiply(a, b) {
        validateInput(a);
        validateInput(b);
        return a * b;
    }
    
    static power(base, exponent) {
        return Math.pow(base, exponent);
    }
}

module.exports = { validateInput, MathHelper };