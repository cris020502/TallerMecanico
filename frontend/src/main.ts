import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import App from './App.vue'

createApp(App).use(createVuetify({ components, directives, theme: { defaultTheme: 'tallerTheme', themes: { tallerTheme: { dark: false, colors: { primary: '#0b5cab', secondary: '#ffb300' } } } }})).mount('#app')
