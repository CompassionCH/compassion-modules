var o=Object.defineProperty;var r=(e,a,t)=>a in e?o(e,a,{enumerable:!0,configurable:!0,writable:!0,value:t}):e[a]=t;var s=(e,a,t)=>(r(e,typeof a!="symbol"?a+"":a,t),t);import{x as d,C as n,B as m,m as i,u as h}from"./index.79c05fa8.js";import{D as f,T as c}from"./TableHeader.e10a13ea.js";import{T as b}from"./TranslatorModal.0abf5672.js";import"./TranslationSkills.c9d4f6f3.js";var p=d`<div>
  <TranslatorModal translatorId="state.modalTranslatorId" onClose="() => this.state.modalTranslatorId = undefined" />
  <div class="container mx-auto px-10 lg:px-0">
    <div class="py-10">
      <h3 class="text-slate-600 font-light text-2xl mb-1">Compassion</h3>
      <h1 class="text-slate-700 font-light text-5xl">Registered Translators</h1>
    </div>
    <div class="relative bg-white rounded-sm shadow-lg flex-1 overflow-hidden mb-10">
      <DAOTable key="'users-page-table'"
        columns="state.columns"
        keyCol="'translatorId'"
        dao="dao"
        onRowClick="(item) => this.state.modalTranslatorId = item.translatorId" />
    </div>
  </div>
</div>`;const x=[{name:"translatorId",header:"ID",searchable:!1,sortable:!1},{name:"name",header:"Name",sortable:!1},{name:"email",header:"E-Mail",sortable:!1},{name:"role",header:"Role",searchable:!1,sortable:!1},{name:"age",header:"Age",sortable:!1},{name:"lastYear",header:"Last Year"},{name:"year",header:"This Year"},{name:"total",header:"Total"},{name:"language",header:"Language",searchable:!1,translatable:!1,sortable:!1}];class l extends n{constructor(){super(...arguments);s(this,"dao",i.translators);s(this,"state",h({columns:x,modalTranslatorId:void 0}))}}s(l,"template",p),s(l,"components",{DAOTable:f,Button:m,TranslatorModal:b,TableHeader:c});export{l as default};
