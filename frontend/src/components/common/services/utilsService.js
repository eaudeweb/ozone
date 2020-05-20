import fromExponential from 'from-exponential/dist/index.min.js'
import { Decimal } from 'decimal.js'

const filterObject = (obj, predicate) => {
  const result = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key) && !predicate(obj[key])) {
      result[key] = obj[key]
    }
  }
  return result
}

const getObjectValue = (path, obj) => {
  const result = path.split('.').reduce((prev, curr, index) => {
    if (Array.isArray(prev)) {
      const newObj = {}
      newObj[prev] = []
      prev.forEach(pr => {
        if (path.split('.').length - 1 === index) {
          newObj[prev] = pr[curr]
        } else {
          newObj[prev].push(pr[curr])
        }
      })
      return prev ? newObj[prev] : undefined
    }
    return prev ? prev[curr] : undefined
  }, obj || self)

  return result
}

const getLevel2PropertyValue = (obj, level2PropertyKey) => {
  if (!obj || !level2PropertyKey) {
    return undefined
  }
  const level1Keys = Object.keys(obj)
  for (let i = 0; i < level1Keys.length; i += 1) {
    const level1Key = level1Keys[i]
    const propertyValue = obj[level1Key][level2PropertyKey]
    if (obj[level1Key][level2PropertyKey] !== undefined) {
      return propertyValue
    }
  }
  return undefined
}

const debounce = (func, wait, immediate) => {
  let timeout
  // eslint-disable-next-line func-names
  return function () {
    const context = this
    // eslint-disable-next-line prefer-rest-params
    const args = arguments
    // eslint-disable-next-line func-names
    const later = function () {
      timeout = null
      if (!immediate) func.apply(context, args)
    }
    const callNow = immediate && !timeout
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
    if (callNow) func.apply(context, args)
  }
}

const isObject = (value) => !!(value && typeof value === 'object' && value.constructor === Object)

const pushUnique = (array, item) => {
  if (!array) {
    return
  }
  if (array.indexOf(item) === -1) {
    array.push(item)
  }
}

const intersect = (a, b) => {
  const setA = new Set(a)
  const setB = new Set(b)
  const intersection = new Set([...setA].filter(x => setB.has(x)))
  return Array.from(intersection)
}

const getPropertyValue = (obj, propertyPath) => {
  if (!obj || !propertyPath) {
    return undefined
  }
  if (!isObject(obj)) {
    return undefined
  }

  return getObjectValue(propertyPath, obj)
}

const isNumber = (n) => !isNaN(parseFloat(n)) && isFinite(n)

const sortAscending = (array, propertyName) => {
  if (!Array.isArray(array)) {
    return null
  }
  return array.sort((x, y) => {
    let valueX = x
    let valueY = y
    if (propertyName) {
      valueX = x[propertyName]
      valueY = y[propertyName]
    }
    if (valueX < valueY) return -1
    if (valueX > valueY) return 1
    return 0
  })
}

const sortDescending = (array, propertyName) => {
  if (!Array.isArray(array)) {
    return null
  }
  return array.sort((x, y) => {
    let valueX = x
    let valueY = y
    if (propertyName) {
      valueX = x[propertyName]
      valueY = y[propertyName]
    }
    if (valueX > valueY) return -1
    if (valueX < valueY) return 1
    return 0
  })
}

const getObjectLevel1PropertyValuesAsArray = (obj, addedPropNameForKey) => {
  const result = []
  if (!obj) {
    return result
  }
  Object.keys(obj).forEach(level1Key => {
    const objLevel1Value = obj[level1Key]
    if (!addedPropNameForKey) {
      result.push(objLevel1Value)
    } else {
      const objWithPropNameForKey = {}
      objWithPropNameForKey[addedPropNameForKey] = level1Key
      if (isObject(objLevel1Value)) {
        result.push({
          ...objLevel1Value,
          ...objWithPropNameForKey
        })
      } else {
        result.push({
          value: objLevel1Value,
          ...objWithPropNameForKey
        })
      }
    }
  })
  return result
}

const valueConverter = (item) => {
  if (item === null || item === undefined || Number.isNaN(parseFloat(item))) {
    return 0
  }
  return parseFloat(item)
}

const doSum = (sumItems) => sumItems.reduce((sum, item) => Decimal.add(valueConverter(item), valueConverter(sum)).toNumber())

const escapeHTML = (html) => {
  const text = document.createTextNode(html)
  const p = document.createElement('p')
  p.appendChild(text)
  return p.innerHTML
}

export {
  filterObject,
  getObjectValue,
  getLevel2PropertyValue,
  isObject,
  pushUnique,
  intersect,
  getPropertyValue,
  isNumber,
  fromExponential,
  sortAscending,
  sortDescending,
  getObjectLevel1PropertyValuesAsArray,
  valueConverter,
  doSum,
  debounce,
  escapeHTML
}
