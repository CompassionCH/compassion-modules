var k=Object.defineProperty;var w=(l,r,t)=>r in l?k(l,r,{enumerable:!0,configurable:!0,writable:!0,value:t}):l[r]=t;var e=(l,r,t)=>(w(l,typeof r!="symbol"?r+"":r,t),t);import{C as p,x as n,I as x,_ as g,u as f,o as v,r as I,d as C,L as D,e as F,n as T}from"./index.79c05fa8.js";class h extends p{}e(h,"template",n`
    <div class="w-4 h-4 flex items-center justify-center rounded cursor-pointer border-solid border shadow-sm focus:border-blue-300 focus:ring focus:ring-offset-0 focus:ring-blue-200 focus:ring-opacity-50" t-att-class="{
      'bg-compassion border-compassion': props.checked,
      'bg-white border-gray-300': !props.checked,
    }" t-on-click.stop="props.onClick">
      <Icon icon="'check'" class="'text-xs text-white'" t-if="props.checked" />
    </div>
  `),e(h,"props",["onClick","checked"]),e(h,"components",{Icon:x});var S=h;const O={data:{type:Object},columns:{type:Array},onClick:{type:Function,optional:!0},onToggle:{type:Function,optional:!0},selectable:{type:Boolean,optional:!0},selected:{type:Boolean,optional:!0},last:{type:Boolean}};class d extends p{constructor(){super(...arguments);e(this,"_",g)}}e(d,"template",n`
    <tr t-on-click="props.onClick ? (() => props.onClick(props.data)) : (() => null)"
      t-att-class="{'hover:bg-slate-300 transition-colors cursor-pointer': props.onClick !== undefined}"
    >
      <td t-if="props.selectable" class="p-3" t-att-class="{'border-b border-solid border-slate-200': !props.last}">
        <Checkbox onClick="props.onToggle" checked="props.selected" />
      </td>
      <t t-foreach="props.columns" t-as="col" t-key="col.name">
        <td class="text-slate-700 py-3 px-1" t-att-class="{
          'border-b border-solid border-slate-200': !props.last,
          'pl-4': col_first,
          'px-3 pr-4': col_last,
          'px-3': !col_fist and !col_last,
        }">
          <span t-if="col.formatter" t-out="col.formatter(props.data[col.name], props.data)" />
          <t t-elif="col.component">
            <t t-set="component" t-value="col.component(props.data[col.name], props.data)" />
            <t t-if="component" t-component="component.component" t-props="component.props" />
          </t>
          <span t-elif="col.translatable === true" t-esc="_(props.data[col.name])" />
          <span t-else="" t-esc="props.data[col.name]" />
        </td>
      </t>
    </tr>
  `),e(d,"props",O),e(d,"defaultProps",{onToggle:()=>null}),e(d,"components",{Checkbox:S});var N=n`<div class="relative">
  <div class="overflow-hidden">
    <table t-att-class="props.class" class="w-full text-sm">
      <thead>
        <tr>
          <td t-if="props.onSelect !== undefined" class="font-medium text-slate-800 px-3 py-4 border-b border-solid border-slate-300 bg-slate-100">
            <Checkbox onClick="() => this.toggleAll()" checked="state.allSelectedIds" />
          </td>
          <td t-foreach="state.columns" t-as="col" t-key="col.name"
            class="p-4 font-medium border-b border-solid border-slate-300" t-att-class="{
              'cursor-pointer': col.sortable !== false,
              'bg-white': props.onSelect === undefined,
              'bg-slate-100': props.onSelect !== undefined,
            }"
            t-on-click="() => this.updateSortOrder(col.name)"
          >
            <div class="flex">
              <span t-esc="_(col.header || col.name)" class="font-medium text-slate-800" />
              <SortOrderViewer t-if="col.sortable !== false" order="filters.sortBy === col.name ? filters.sortOrder : undefined" />
            </div>
          </td>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td t-if="props.onSelect !== undefined" class="bg-slate-200 border-b border-solid border-slate-300" />
          <td t-foreach="state.columns" t-as="col" t-key="col.name" class="bg-slate-200 border-b border-solid border-slate-300">
            <t t-set="searchFilter" t-value="this.filters.search.find(it => it.column === col.name)" />
            <input type="text" t-att-placeholder="_('Search ') + _(col.header || col.name)" t-if="col.searchable !== false" t-on-input="(e) => this.searchColumn(col.name, e)" t-att-value="searchFilter ? searchFilter.term : ''"
              class="outline-none w-full py-1 px-3 text-xs text-slate-800 border border-transparent focus:border-compassion focus:bg-white focus:shadow-lg border-none" t-att-class="{
                'bg-slate-200': !searchFilter or searchFilter.term.trim() === '',
                'bg-yellow-300 text-yellow-800': searchFilter and searchFilter.term.trim() !== '',
              }" />
          </td>
        </tr>
        <tr t-if="state.pageData.length === 0 and !state.loading">
          <td t-att-colspan="state.columns.length + (props.onSelect === undefined ? 0 : 1)">
            <div class="flex items-center flex-col p-6">
              <Icon icon="'otter'" class="'text-5xl text-blue-400'" />
              <p class="text-slate-600 text-lg">No Result</p>
            </div>
          </td>
        </tr>
        <t t-foreach="state.pageData" t-as="row" t-key="row[props.keyCol]">
          <Row columns="state.columns"
            data="row"
            onClick="props.onRowClick"
            selected="state.selectedIds.includes(row[props.keyCol])"
            selectable="props.onSelect !== undefined"
            last="row_last"
            onToggle="() => this.toggleItem(row[props.keyCol])" />
        </t>
      </tbody>
    </table>
  </div>
  <div class="flex justify-between items-center border-t border-solid border-slate-300 p-4" t-if="state.pageData.length > 0">
    <div class="flex">
      <div class="text-slate-700 text-sm">
        Showing 
        <t t-esc="(filters.pageNumber * state.pageData.length) + 1" /> - <t t-esc="(filters.pageNumber + 1) * state.pageData.length" />
        of <t t-esc="state.total" /> Results
      </div>
      <p t-on-click="() => this.clearFilters()" t-if="filters.search.length > 0 || filters.sortBy !== undefined" class="text-sm text-red-700 hover:text-red-900 cursor-pointer ml-2">Clear filters</p>
    </div>
    <div>
      <PageSelector page="filters.pageNumber" total="state.total" pageSize="filters.pageSize" onPageChange="(page) => this.changePage(page)" />
    </div>
  </div>
  <Transition active="state.loading" t-slot-scope="scope">
    <div class="absolute top-0 left-0 w-full h-full bg-white-50 backdrop-filter backdrop-blur flex justify-center items-center" t-att-class="scope.itemClass">
      <div class="bg-white p-8 shadow-xl">
        <Loader class="'text-4xl'" />
      </div>
    </div>
  </Transition>
</div>`;const _={page:{type:Number},total:{type:Number},pageSize:{type:Number},onPageChange:{type:Function}};class b extends p{constructor(){super(...arguments);e(this,"state",f({paginationButtons:[],pages:0}))}setup(){this.update(this.props),v(t=>{this.update(t)})}update({page:t,total:s,pageSize:i}){const a=Math.ceil(s/i),o=[];if(a<5)for(let c=0;c<a;c++)o.push({type:"page",id:c});else if(t===0||t===1||t===2){for(let c=0;c<4;c++)o.push({type:"page",id:c});o.push({type:"fill",id:Math.random()}),o.push({type:"page",id:a-1})}else if(t===a-1||t===a-2||t===a-3){o.push({type:"page",id:0}),o.push({type:"fill",id:Math.random()});for(let c=a-3;c<a;c++)o.push({type:"page",id:c})}else o.push({type:"page",id:0}),o.push({type:"fill",id:Math.random()}),o.push({type:"page",id:t-1}),o.push({type:"page",id:t}),o.push({type:"page",id:t+1}),o.push({type:"fill",id:Math.random()}),o.push({type:"page",id:a-1});this.state.paginationButtons=o}}e(b,"template",n`
    <div class="flex">
      <t t-foreach="state.paginationButtons" t-as="btn" t-key="btn.id">
        <div class="mr-1">
          <button t-if="btn.type === 'page'"
            t-esc="btn.id + 1"
            t-on-click="() => props.page === btn.id ? null : props.onPageChange(btn.id)"
            class="w-7 h-7 flex justify-center items-center transition-colors rounded-sm text-sm"
            t-att-class="{
              'bg-compassion shadow-inner text-white': btn.id === props.page,
              'text-slate-700 hover:bg-black-20': btn.id !== props.page,
            }" />
          <span t-else=""
            t-esc="'...'"
            class="w-7 h-7 flex text-xs justify-center items-center text-slate-500" />
        </div>
      </t>
    </div>
  `),e(b,"props",_);var B=b;class u extends p{}e(u,"template",n`
    <div class="flex flex-col relative ml-2 text-slate-800 text-xs">
      <Icon icon="'caret-up'" class="{
        'h-1.5': true,
        'opacity-30': props.order !== 'asc',
      }" />
      <Icon icon="'caret-down'" class="{
        'h-1': true,
        'opacity-30': props.order !== 'desc',
      }" />
    </div>
  `),e(u,"components",{Icon:x}),e(u,"props",{order:{type:String,optional:!0}});var P=u;const j=(l,r,t=window.localStorage)=>{if(!r)return f(l);const s=t.getItem(r),i=s?JSON.parse(s):l,a=I(f(i),()=>{t.setItem(r,JSON.stringify(a))});return a};var $=j;const M={key:{type:String,optional:!0},columns:{type:Array},keyCol:{type:String},dao:{type:Object},onSelect:{type:Function,optional:!0},class:{type:String,optional:!0},onRowClick:{type:Function,optional:!0},baseDomain:{type:Function,optional:!0}};class m extends p{constructor(){super(...arguments);e(this,"_",g);e(this,"state",f({columns:[],selectedIds:[],allSelectedIds:!1,pageData:[],searchTimeout:void 0,loading:!1,total:0}));e(this,"filters",$({pageNumber:0,pageSize:10,search:[],sortBy:void 0,sortOrder:"desc"},this.props.key))}setup(){this.update(this.props),F(()=>{this.updateData()}),v(t=>{this.update(t)})}toggleAll(){this.state.allSelectedIds?(this.state.allSelectedIds=!1,this.state.selectedIds=[],this.props.onSelect&&this.props.onSelect(this.state.selectedIds)):(this.state.loading=!0,this.props.dao.listIds||(console.error("Given DAO does not implement listIds!"),T.error(g("Unable to perform this operation"))),this.props.dao.listIds(this.filters).then(t=>{this.state.selectedIds=t,this.state.allSelectedIds=!0,this.state.loading=!1,this.props.onSelect&&this.props.onSelect(this.state.selectedIds)}))}clearFilters(){this.filters.search=[],this.filters.pageNumber=0,this.filters.sortBy=void 0,this.filters.sortOrder="desc",this.updateData()}toggleItem(t){const s=this.state.selectedIds.indexOf(t);s>=0?this.state.selectedIds.splice(s,1):this.state.selectedIds.push(t),this.state.allSelectedIds=!1,this.props.onSelect&&this.props.onSelect(this.state.selectedIds)}async updateData(t=this.filters){this.state.loading=!0;const s=this.props.baseDomain?await this.props.baseDomain():[];t.search=[...s,...t.search],console.log(s,t);const i=await this.props.dao.list(t);this.state.pageData=i.data,this.state.total=i.total,this.state.loading=!1}changePage(t){this.filters.pageNumber=t,this.updateData()}searchColumn(t,s){this.state.searchTimeout&&clearTimeout(this.state.searchTimeout),this.state.allSelectedIds=!1,this.state.selectedIds=[],this.props.onSelect&&this.props.onSelect(this.state.selectedIds),this.state.searchTimeout=setTimeout(()=>{const i=s.target.value,a=this.filters.search.findIndex(o=>o.column===t);i.trim()===""&&a>=0?this.filters.search.splice(a,1):a>=0?this.filters.search[a].term=i:this.filters.search.push({column:t,term:i}),clearTimeout(this.state.searchTimeout),this.state.searchTimeout=void 0,this.filters.pageNumber=0,this.updateData()},500)}updateSortOrder(t){const s=this.state.columns.find(i=>i.name===t);!s||s.sortable===!1||(this.filters.sortOrder==="asc"?this.filters.sortOrder="desc":this.filters.sortOrder="asc",this.filters.sortBy=t,this.updateData())}update({columns:t}){this.state.columns=t.map(s=>typeof s=="string"?{header:s,name:s}:s)}}e(m,"template",N),e(m,"props",M),e(m,"components",{Row:d,Transition:C,PageSelector:B,Loader:D,Icon:x,SortOrderViewer:P,Checkbox:S});class y extends p{}e(y,"template",n`
    <div class="flex justify-between border-b border-solid border-slate-200 py-4 px-2 items-center">
      <p class="transition text-sm px-2" t-att-class="{
        'text-slate-400': props.selected === 0,
        'text-slate-800': props.selected > 0,
      }">
        <span t-esc="props.selected" /> <span t-esc="props.name || 'Items'" /> Selected
      </p>
      <div class="flex items-center pr-2">
        <t t-slot="default" />
      </div>
    </div>
  `),e(y,"props",{selected:{type:Number},name:{type:String,optional:!0},"*":{}});var L=y;export{m as D,L as T};
