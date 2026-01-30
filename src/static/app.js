document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const categoryFilters = document.getElementById("category-filters");
  
  let allActivities = {};
  let currentFilter = "all";

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      allActivities = await response.json();

      // Extract unique categories
      const categories = [...new Set(Object.values(allActivities).map(a => a.category))];
      
      // Add event listener to "All Activities" button
      const allActivitiesBtn = categoryFilters.querySelector('[data-category="all"]');
      if (allActivitiesBtn) {
        allActivitiesBtn.addEventListener("click", () => filterActivities("all"));
      }
      
      // Create category filter buttons
      categories.forEach(category => {
        const btn = document.createElement("button");
        btn.className = "filter-btn";
        btn.dataset.category = category.toLowerCase();
        btn.textContent = category;
        btn.addEventListener("click", () => filterActivities(category.toLowerCase()));
        categoryFilters.appendChild(btn);
      });

      // Display all activities initially
      displayActivities();
      populateActivitySelect();
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Function to display activities based on current filter
  function displayActivities() {
    // Clear activities list
    activitiesList.innerHTML = "";

    // Filter and display activities
    Object.entries(allActivities).forEach(([name, details]) => {
      const category = details.category.toLowerCase();
      
      // Apply filter
      if (currentFilter !== "all" && category !== currentFilter) {
        return;
      }

      const activityCard = document.createElement("div");
      activityCard.className = "activity-card";
      activityCard.dataset.category = category;

      const spotsLeft = details.max_participants - details.participants.length;
      const availabilityClass = spotsLeft === 0 ? "full" : spotsLeft < 5 ? "limited" : "";
      const availabilityText = spotsLeft === 0 ? "Full" : `${spotsLeft} spots left`;

      activityCard.innerHTML = `
        <h4>
          ${name}
          <span class="category-badge category-${category}">${details.category}</span>
        </h4>
        <p>${details.description}</p>
        <p><strong>Schedule:</strong> ${details.schedule}</p>
        <p class="availability ${availabilityClass}"><strong>Availability:</strong> ${availabilityText}</p>
      `;

      activitiesList.appendChild(activityCard);
    });

    // Show message if no activities match filter
    if (activitiesList.children.length === 0) {
      activitiesList.innerHTML = "<p>No activities found in this category.</p>";
    }
  }

  // Function to populate activity select dropdown
  function populateActivitySelect() {
    // Clear existing options except the first one
    activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';
    
    Object.entries(allActivities).forEach(([name, details]) => {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = `${name} (${details.category})`;
      activitySelect.appendChild(option);
    });
  }

  // Function to filter activities by category
  function filterActivities(category) {
    currentFilter = category;
    
    // Update active button
    document.querySelectorAll(".filter-btn").forEach(btn => {
      btn.classList.remove("active");
      if (btn.dataset.category === category) {
        btn.classList.add("active");
      }
    });

    displayActivities();
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success message";
        signupForm.reset();
        
        // Refresh activities to show updated availability
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error message";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error message";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
