var m=Object.defineProperty;var o=(s,t,e)=>t in s?m(s,t,{enumerable:!0,configurable:!0,writable:!0,value:e}):s[t]=e;var l=(s,t,e)=>(o(s,typeof t!="symbol"?t+"":t,e),e);import{C as x,x as c,_ as i}from"./index.79c05fa8.js";class a extends x{constructor(){super(...arguments);l(this,"_",i)}}l(a,"template",c`
    <div t-foreach="props.skills" t-as="skill" t-key="skill_index" class="flex items-center mb-3">
      <p t-esc="_(skill.source)" class="text-sm text-slate-700 bg-slate-100 rounded-sm py-2 font-semibold w-28 text-center" />
      <p class="text-slate-500 font-semibold text-sm mx-4">-></p>
      <p t-esc="_(skill.target)" class="text-sm text-slate-700 bg-slate-100 rounded-sm py-2 font-semibold w-28 text-center" />
    </div>
  `),l(a,"props",["skills"]);export{a as T};
