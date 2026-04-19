<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <keep-alive include="Dashboard">
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </div>
</template>

<script setup>
</script>