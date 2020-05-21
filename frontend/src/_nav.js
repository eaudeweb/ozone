const getNav = ($gettext) => [{
  name: $gettext('Dashboard'),
  url: '/dashboard',
  icon: 'icon-screen-desktop'
},
{
  name: $gettext('Reports'),
  icon: 'icon-chart',
  url: '/reports'
},
{
  name: $gettext('Parties'),
  url: '/lookup-tables/parties',
  icon: 'icon-people'
},
{
  name: $gettext('Controlled substances'),
  url: '/lookup-tables/controlled-substances',
  icon: 'icon-chemistry'
},
{
  name: $gettext('Mixtures'),
  url: '/lookup-tables/blends',
  icon: 'icon-layers'
},
{
  name: $gettext('Consumption / production'),
  icon: 'icon-graph',
  url: '/production-consumption'
}
]

export {
  getNav
}
