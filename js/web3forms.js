/**
 * Web3Forms Handler with Multi-Layer Spam Protection
 * - Honeypot field (bot trap)
 * - reCAPTCHA v3 (invisible)
 * - Client-side validation
 * - Web3Forms server-side filtering
 */

class Web3FormsHandler {
    constructor(formId, recaptchaSiteKey) {
        this.form = document.getElementById(formId);
        this.recaptchaSiteKey = recaptchaSiteKey;
        this.submitButton = null;
        this.statusDiv = null;

        if (this.form) {
            this.init();
        }
    }

    init() {
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.statusDiv = document.getElementById('formStatus');

        // Load reCAPTCHA v3
        this.loadRecaptcha();

        // Form submission handler
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    loadRecaptcha() {
        const script = document.createElement('script');
        script.src = `https://www.google.com/recaptcha/api.js?render=${this.recaptchaSiteKey}`;
        script.async = true;
        script.defer = true;
        document.head.appendChild(script);
    }

    async handleSubmit(e) {
        e.preventDefault();

        // Client-side validation
        if (!this.form.checkValidity()) {
            this.showStatus('Please fill in all required fields.', 'error');
            return;
        }

        // Honeypot check (bot detection)
        const honeypot = this.form.querySelector('input[name="botcheck"]');
        if (honeypot && honeypot.checked) {
            // Silent fail for bots - they think it worked but email is NOT sent
            this.showStatus('Thank you! Your message has been sent.', 'success');
            this.form.reset();
            return;
        }

        // Set loading state
        this.setLoadingState(true);
        this.hideStatus();

        try {
            // Get reCAPTCHA token
            const token = await this.getRecaptchaToken();
            document.getElementById('recaptchaResponse').value = token;

            // Submit to Web3Forms
            const formData = new FormData(this.form);
            const response = await fetch('https://api.web3forms.com/submit', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.showStatus('Thank you! Your message has been sent successfully.', 'success');
                this.form.reset();

                // Optional: Analytics tracking
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'form_submit', {
                        'event_category': 'Contact Form',
                        'event_label': 'Success'
                    });
                }
            } else {
                throw new Error(data.message || 'Submission failed');
            }

        } catch (error) {
            console.error('Form submission error:', error);
            this.showStatus(
                'Sorry, there was an error sending your message. Please try again or email us directly.',
                'error'
            );
        } finally {
            this.setLoadingState(false);
        }
    }

    async getRecaptchaToken() {
        return new Promise((resolve, reject) => {
            if (typeof grecaptcha === 'undefined') {
                reject(new Error('reCAPTCHA not loaded'));
                return;
            }

            grecaptcha.ready(() => {
                grecaptcha.execute(this.recaptchaSiteKey, { action: 'submit' })
                    .then(resolve)
                    .catch(reject);
            });
        });
    }

    setLoadingState(isLoading) {
        const btnText = this.submitButton.querySelector('.btn-text');
        const btnLoader = this.submitButton.querySelector('.btn-loader');

        if (isLoading) {
            this.submitButton.disabled = true;
            if (btnText) btnText.style.display = 'none';
            if (btnLoader) btnLoader.style.display = 'inline-block';
        } else {
            this.submitButton.disabled = false;
            if (btnText) btnText.style.display = 'inline';
            if (btnLoader) btnLoader.style.display = 'none';
        }
    }

    showStatus(message, type) {
        if (!this.statusDiv) return;

        this.statusDiv.textContent = message;
        this.statusDiv.className = `form-status ${type}`;
        this.statusDiv.style.display = 'block';

        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => this.hideStatus(), 5000);
        }
    }

    hideStatus() {
        if (this.statusDiv) {
            this.statusDiv.style.display = 'none';
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWeb3Forms);
} else {
    initWeb3Forms();
}

function initWeb3Forms() {
    // reCAPTCHA Site Key (PUBLIC - safe to expose in client-side code)
    const recaptchaSiteKey = window.RECAPTCHA_SITE_KEY || '6Lf_dvwpAAAAAFmtH33BiSaA2Iu6XKM64Fz9qv5w';
    new Web3FormsHandler('contactForm', recaptchaSiteKey);
}
