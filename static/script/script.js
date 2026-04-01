document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    // Toggle between login and register forms
    document.getElementById('switchToRegister')?.addEventListener('click', function() {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
    });

    document.getElementById('switchToLogin')?.addEventListener('click', function() {
        registerForm.style.display = 'none';
        loginForm.style.display = 'block';
    });

    // Login Form Submission
    document.getElementById("loginFormElement")?.addEventListener("submit", function (event) {
        event.preventDefault();
        const emailInput = document.getElementById("loginEmail");
        const passwordInput = document.getElementById("loginPassword");

        if (!emailInput || !passwordInput) {
            alert("Login fields not found.");
            return;
        }

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if (!email.endsWith("@eastdelta.edu.bd")) {
            alert("You must log in with EDU mail");
            return;
        }

        alert("Login successful!");
        localStorage.setItem("userEmail", email);
        window.location.href = "dashboard.html"; // Redirect to dashboard
    });

    // Register Form Submission
    document.getElementById("registerFormElement")?.addEventListener("submit", function (event) {
        event.preventDefault();
        
        const nameInput = document.getElementById("registerName");
        const emailInput = document.getElementById("registerEmail");
        const phoneInput = document.getElementById("registerPhone");
        const passwordInput = document.getElementById("registerPassword");
        const confirmPasswordInput = document.getElementById("registerConfirmPassword");
        const dobInput = document.getElementById("registerDOB");

        // Address Fields
        const streetField = document.getElementById("street");
        const areaField = document.getElementById("area");
        const policeStationField = document.getElementById("policeStation");

        if (!emailInput || !passwordInput || !confirmPasswordInput || !phoneInput || !nameInput || !dobInput || !streetField || !areaField || !policeStationField) {
            alert("Some registration fields are missing.");
            return;
        }

        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        const phone = phoneInput.value.trim();
        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();
        const dob = new Date(dobInput.value);
        const today = new Date();
        const age = today.getFullYear() - dob.getFullYear();

        // Address Validation
        const street = streetField.value.trim();
        const area = areaField.value.trim();
        const policeStation = policeStationField.value.trim();

        if (!email.endsWith("@eastdelta.edu.bd")) {
            alert("You must register with EDU mail");
            return;
        }

        if (!/^\d{11}$/.test(phone)) {
            alert("Phone number must be exactly 11 digits!");
            return;
        }

        if (password.length < 8) {
            alert("Password must be at least 8 characters long!");
            return;
        }

        if (password !== confirmPassword) {
            alert("Passwords do not match!");
            return;
        }

        if (age < 18) {
            alert("You must be at least 18 years old to register!");
            return;
        }

        if (!street || !area || !policeStation) {
            alert("Address fields cannot be empty!");
            return;
        }

        alert("Registration successful! Redirecting to login page...");
        window.location.href = "login.html"; // Redirect to login page
    });

    // Address Field Auto-Fill
    const addressField = document.getElementById("address");
    const streetField = document.getElementById("street");
    const areaField = document.getElementById("area");
    const policeStationField = document.getElementById("policeStation");

    function updateAddress() {
        addressField.value = `${streetField.value}, ${areaField.value}, ${policeStationField.value}, Chattogram`;
    }

    streetField?.addEventListener("input", updateAddress);
    areaField?.addEventListener("input", updateAddress);
    policeStationField?.addEventListener("input", updateAddress);

    // ✅ Login Check for Donate and Seek Blood Buttons
    const userLoggedIn = localStorage.getItem("userEmail");

    const donateBtn = document.querySelector(".cta-buttons a[href='findDonor.html']");
    const seekBtn = document.querySelector(".cta-buttons a[href='reqBlood.html']");

    function redirectToLogin(event) {
        event.preventDefault();
        window.location.href = "login.html?message=login_required";
    }

    if (!userLoggedIn) {
        donateBtn?.addEventListener("click", redirectToLogin);
        seekBtn?.addEventListener("click", redirectToLogin);
    }

    // ✅ Show login-required message
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("message") === "login_required") {
        alert("You must log in first to donate or seek blood.");
    }
});
