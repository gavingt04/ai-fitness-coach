<template>
  <router-view />
</template>

<style>
/* 全局基础样式，适配移动端，抹平浏览器默认边距 */
body, html {
  margin: 0;
  padding: 0;
  background-color: #f7f8fa; /* 稍微带点灰色的背景，显得更有质感 */
  height: 100%;
}
#app {
  height: 100%;
}
</style>