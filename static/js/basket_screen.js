const shell = document.querySelector(".basket-screen");

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return "";
}

function money(value, currency = "USD") {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function setError(message) {
  const errorBox = document.getElementById("basket-error");
  if (!message) {
    errorBox.classList.add("d-none");
    errorBox.textContent = "";
    return;
  }
  errorBox.textContent = message;
  errorBox.classList.remove("d-none");
}

function statusClass(status) {
  return `status-pill status-${status}`;
}

function renderBasket(data) {
  const items = data.items || [];
  const currency = items[0]?.currency || "USD";
  const itemsNode = document.getElementById("basket-items");
  const emptyNode = document.getElementById("basket-empty");
  const countNode = document.getElementById("item-count");
  const totalNode = document.getElementById("basket-total");
  const statusNode = document.getElementById("basket-status");
  const finishButton = document.getElementById("finish-basket");
  const qrZone = document.getElementById("qr-zone");
  const qrCode = document.getElementById("qr-code");
  const checkoutLink = document.getElementById("checkout-link");

  itemsNode.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("article");
    row.className = "basket-item";
    row.innerHTML = `
      <span>
        <strong>${item.product_name}</strong>
        <small>${item.category} - confiance ${item.last_confidence}</small>
      </span>
      <span class="item-money">
        <strong>${money(item.subtotal, item.currency)}</strong>
        <small>${item.quantity} x ${money(item.unit_price, item.currency)}</small>
      </span>
    `;
    itemsNode.appendChild(row);
  });

  emptyNode.classList.toggle("d-none", items.length > 0);
  countNode.textContent = `${items.length} ligne${items.length > 1 ? "s" : ""}`;
  totalNode.textContent = money(data.total_amount, currency);
  statusNode.textContent = data.status;
  statusNode.className = statusClass(data.status);

  const canFinish = data.status === "active" && items.length > 0;
  finishButton.disabled = !canFinish;
  finishButton.textContent = data.status === "pending_checkout" ? "Panier termine" : "Terminer le panier";

  if (data.qr_code_url && data.checkout_url) {
    qrCode.src = data.qr_code_url;
    checkoutLink.href = data.checkout_url;
    qrZone.classList.remove("d-none");
  } else {
    qrZone.classList.add("d-none");
  }
}

async function refreshBasket() {
  if (!shell) return;
  try {
    const response = await fetch(shell.dataset.detailUrl, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("Impossible de charger le panier.");
    renderBasket(await response.json());
    setError("");
  } catch (error) {
    setError(error.message);
  }
}

async function finishBasket() {
  try {
    const response = await fetch(shell.dataset.finishUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({}),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Impossible de terminer ce panier.");
    renderBasket(data.basket);
    setError("");
  } catch (error) {
    setError(error.message);
  }
}

if (shell) {
  document.getElementById("finish-basket").addEventListener("click", finishBasket);
  refreshBasket();
  window.setInterval(refreshBasket, 1000);
}
