var h=Object.defineProperty;var b=(s,a,t)=>a in s?h(s,a,{enumerable:!0,configurable:!0,writable:!0,value:t}):s[a]=t;var e=(s,a,t)=>(b(s,typeof a!="symbol"?a+"":a,t),t);import{x as n,C as i,b as c,R as f,B as x,m as v,u as g,_ as p,n as y,c as T}from"./index.79c05fa8.js";import{D as k,T as w}from"./TableHeader.e10a13ea.js";import{T as C}from"./TranslatorButton.809c59a7.js";import"./TranslatorModal.0abf5672.js";import"./TranslationSkills.c9d4f6f3.js";var D=n`<div>
  <div class="container mx-auto">
    <div class="py-10">
      <h3 class="text-slate-600 font-light text-2xl mb-1">Compassion</h3>
      <h1 class="text-slate-700 font-light text-5xl">Available Letters</h1>
    </div>
    <div class="bg-white rounded-sm shadow-lg flex-1 overflow-hidden mb-10">
      <DAOTable key="'letters-page-table'"
          columns="state.columns"
          keyCol="'id'"
          dao="dao" />
    </div>
  </div>
</div>`;class l extends i{}e(l,"props",["priority"]),e(l,"template",n`<div class="text-xs w-5 h-5 flex items-center justify-center rounded" t-esc="props.priority" t-att-class="{
    'bg-slate-100 text-slate-600': props.priority === 0,
    'bg-slate-300 text-slate-700': props.priority === 1,
    'bg-orange-600 text-white': props.priority === 2,
    'bg-red-500 text-white': props.priority === 3,
    'bg-red-700 text-white': props.priority === 4
  }" />`);class o extends i{constructor(){super(...arguments);e(this,"currentTranslator",c())}}e(o,"template",n`
    <div class="flex gap-1 pl-3">
      <t t-if="currentTranslator.data.role === 'admin'">
        <RouterLink to="'/letters/letter-view/' + props.letter.id">
          <button class="text-blue-500 hover:text-compassion transition-colors">View</button>
        </RouterLink>
        <span class="text-slate-600">·</span>
      </t>
      <RouterLink to="'/letters/letter-edit/' + props.letter.id">
        <button class="text-blue-500 hover:text-compassion transition-colors">Translate</button>
      </RouterLink>
    </div>
  `),e(o,"props",{letter:{type:Object}}),e(o,"components",{RouterLink:f});var m;class d extends i{constructor(){super(...arguments);e(this,"translator",c());e(this,"dao",v.letters);e(this,"state",g({loading:!1,columns:[{name:"priority",component:t=>({component:l,props:{priority:t}})},"title","status",{name:"unreadComments",header:"Comments",formatter:t=>p(t?"Yes":"No")},{name:"source",translatable:!0,sortable:!1},{name:"target",translatable:!0,sortable:!1},...((m=this.translator.data)==null?void 0:m.role)==="admin"?[{name:"translatorId",header:"Translator",component:t=>t?{component:C,props:{translatorId:t}}:null}]:[],{name:"date",searchable:!1,formatter:t=>t.toLocaleDateString()},{name:"actions",searchable:!1,sortable:!1,component:(t,r)=>({component:o,props:{letter:r}})}]}))}setup(){this.state.loading=!0,this.translator.loadIfNotInitialized().then(()=>{var t,r;((t=this.translator.data)==null?void 0:t.role)!=="admin"&&((r=this.translator.data)==null?void 0:r.skills.filter(u=>u.verified).length)===0&&(this.state.loading=!1,y.error(p("You cannot list letters while having 0 verified translation skill")),T("/"))})}}e(d,"template",D),e(d,"components",{DAOTable:k,Button:x,TableHeader:w});export{d as default};
