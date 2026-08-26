/* =========================================
   FraudShield — Login
   ========================================= */

document.addEventListener("DOMContentLoaded", () => {

    const loginForm = document.getElementById("login-form");
    const emailInput = document.getElementById("login-email");
    const passwordInput = document.getElementById("login-password");
    const forgotPasswordBtn = document.getElementById("forgot-password-btn");


    // =========================================
    // Login
    // =========================================

    loginForm.addEventListener("submit", (event) => {

        event.preventDefault();

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();


        // =========================================
        // Basic Validation
        // =========================================

        if (!email || !password) {

            alert("Please enter your email and password.");

            return;
        }


        // =========================================
        // Demo Authentication
        // =========================================

        /*
         * Temporary demo login.
         *
         * We will replace this with the real
         * authentication system when the backend
         * is connected.
         */

        const demoEmail = "admin@fraudshield.com";
        const demoPassword = "admin123";


        if (
            email === demoEmail &&
            password === demoPassword
        ) {

            // Store login state
            sessionStorage.setItem(
                "fraudshield_logged_in",
                "true"
            );


            // Redirect to dashboard
            window.location.href = "../index.html";

        } else {

            alert("Invalid email or password.");

        }

    });


    // =========================================
    // Forgot Password
    // =========================================

    forgotPasswordBtn.addEventListener("click", () => {

        alert(
            "Password reset functionality will be available soon."
        );

    });

});