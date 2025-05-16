<template>
  <div>
    <ThemeToggle />
    <Sidebar />
  <div class="about-container">
    <div class="about-header">
      <h1>About LaptopAdvisor</h1>
    </div>

    <div class="about-content">
      <section class="about-section">
        <h2>Our Mission</h2>
        <p>
          LaptopAdvisor aims to simplify your laptop buying experience by providing
          personalized recommendations based on your specific needs, preferences, and budget.
        </p>
      </section>

      <section class="about-section">
        <h2>How It Works</h2>
        <p>
          Our AI-powered chat assistant asks you questions about your intended use,
          preferences, and budget constraints. Based on your responses, we analyze thousands
          of laptop models to find the best matches for your requirements.
        </p>
      </section>

      <section class="about-section">
        <h2>Our Team</h2>
        <ul>
          <li>River Amoss - Frontend Developer and Designer</li>
          <li>Rosslan Koulli - AI Specialist and Developer</li>
          <li>Samuel Sutcliffe - Database and Sever Engineer</li>
          <li>Mamoon Mamoon - Data Engineer and Analyst</li>
          <li>Zain Ahed - Test Specialist and Researcher</li>
        </ul>

        <p>
          LaptopAdvisor was developed by a team of tech enthusiasts and AI specialists
          dedicated to making technology choices simpler for everyone.
        </p>
      </section>

    </div>
  </div>
  </div>
</template>

<script setup>
// No specific logic needed for this page
</script>

<style>
.about-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.about-header {
  text-align: center;
  margin-bottom: 2rem;
}

.about-section {
  margin-bottom: 2rem;
}

.about-section h2 {
  color: var(--primary-color, #4a6ee0);
  margin-bottom: 1rem;
}
.about-section ul {
  list-style-type: disc;
  padding-left: 1.5rem;
}
.about-section li {
  margin-bottom: 0.5rem;
}

.about-section p {
  line-height: 1.6;
}
</style>