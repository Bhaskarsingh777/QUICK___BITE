document.addEventListener("DOMContentLoaded", function () {

    // ===========================
    // LOGIN STATUS
    // ===========================
    const isLoggedIn = document.body.dataset.loggedIn === "True";

    // ===========================
    // MODAL ELEMENTS
    // ===========================
    const loginModal = document.getElementById("loginModal");
    const signupModal = document.getElementById("signupModal");
    const orderModal = document.getElementById("orderModal");
    const reviewModal = document.getElementById("reviewModal");

    // Buttons
    const loginBtn = document.getElementById("loginBtn");
    const signupBtn = document.getElementById("signupBtn");
    const closeLogin = document.getElementById("closeLogin");
    const closeSignup = document.getElementById("closeSignup");
    const closeOrder = document.getElementById("closeOrder");
    const closeReview = document.getElementById("closeReview");
    const addReviewBtn = document.getElementById("addReviewBtn");

    const toSignup = document.getElementById("toSignup");
    const toLogin = document.getElementById("toLogin");

    const orderItem = document.getElementById("orderItem");
    const orderPrice = document.getElementById("orderPrice");
    const quantityInput = document.querySelector("#orderModal input[name='quantity']");

    // ===========================
    // SHOW / HIDE FUNCTION
    // ===========================
    function showModal(modal) {
        if (!modal) return;
        modal.style.display = "flex";
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
    }

    function hideModal(modal) {
        if (!modal) return;
        modal.style.display = "none";
        modal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "auto";
    }

    // ===========================
    // LOGIN MODAL
    // ===========================
    loginBtn?.addEventListener("click", () => showModal(loginModal));
    closeLogin?.addEventListener("click", () => hideModal(loginModal));

    // ===========================
    // SIGNUP MODAL
    // ===========================
    signupBtn?.addEventListener("click", () => showModal(signupModal));
    closeSignup?.addEventListener("click", () => hideModal(signupModal));

    // ===========================
    // SWITCH LOGIN <-> SIGNUP
    // ===========================
    toSignup?.addEventListener("click", () => {
        hideModal(loginModal);
        showModal(signupModal);
    });

    toLogin?.addEventListener("click", () => {
        hideModal(signupModal);
        showModal(loginModal);
    });

    // ===========================
    // ORDER BUTTON (LOGIN REQUIRED)
    // ===========================
    document.querySelectorAll(".orderBtn").forEach(button => {
        button.addEventListener("click", function () {

            if (!isLoggedIn) {
                alert("Please login first to place order!");
                showModal(loginModal);
                return;
            }

            const item = this.dataset.item;
            const price = this.dataset.price;

            if (orderItem) orderItem.value = item || "";
            if (orderPrice) orderPrice.value = price || "";
            if (quantityInput) quantityInput.value = 1;

            showModal(orderModal);
        });
    });

    closeOrder?.addEventListener("click", () => hideModal(orderModal));

    // ===========================
    // REVIEW MODAL
    // ===========================
    addReviewBtn?.addEventListener("click", () => showModal(reviewModal));
    closeReview?.addEventListener("click", () => hideModal(reviewModal));

    // ===========================
    // CLICK OUTSIDE TO CLOSE
    // ===========================
    window.addEventListener("click", (e) => {
        if (e.target === loginModal) hideModal(loginModal);
        if (e.target === signupModal) hideModal(signupModal);
        if (e.target === orderModal) hideModal(orderModal);
        if (e.target === reviewModal) hideModal(reviewModal);
    });

    // ===========================
    // SEARCH FILTER
    // ===========================
    const searchInput = document.getElementById("searchInput");
    const foodItems = document.querySelectorAll(".item");

    searchInput?.addEventListener("keyup", function () {
        const value = this.value.toLowerCase();

        foodItems.forEach(item => {
            const nameElement = item.querySelector("h4");
            if (!nameElement) return;

            const name = nameElement.innerText.toLowerCase();
            item.style.display = name.includes(value) ? "block" : "none";
        });
    });

    // ===========================
    // PAYMENT POPUP (NEW SECTION)
    // ===========================
    const paymentForm = document.getElementById("paymentForm");
    const successPopup = document.getElementById("successPopup");

    if (paymentForm) {
        paymentForm.addEventListener("submit", function (e) {
            e.preventDefault();

            fetch("/confirm_payment", {
                method: "POST"
            })
            .then(response => response.text())
            .then(() => {
                if (successPopup) {
                    successPopup.style.display = "flex";
                }
            });
        });
    }

});