const _matches = ['matches', 'webkitMatchesSelector', 'mozMatchesSelector', 'msMatchesSelector', 'matchesSelector']

const nodeListPrototypes = () => {
  if (window.NodeList) {
    if (!NodeList.prototype.forEach) {
      NodeList.prototype.forEach = Array.prototype.forEach
    }
  }
}

Element.prototype.msMatchesSelector = Element.prototype.matches

const nodePrototypes = () => {
  if (window.Node) {
    if (!Node.prototype.contains) {
      // eslint-disable-next-line
      Node.prototype.contains = function (node) {
        if (!node) {
          throw new TypeError('1 argument is required')
        }
        do {
          if (this === node) {
            return true
          }
          node = node && node.parentNode
        } while (node)
        return false
      }
    }
  }
}

const elementMatchesPrototype = () => {
  _matches.forEach(matchesPrototype => {
    if (!Element.prototype[matchesPrototype]) {
      // eslint-disable-next-line
      Element.prototype[matchesPrototype] = function (selector) {
        const element = this
        const potentialMatches = element.parentNode.querySelectorAll(selector)
        let i = potentialMatches.length

        // Loop back through each item found and match it against the element being checked
        // eslint-disable-next-line
        while (--i >= 0) {
          if (potentialMatches.item(i) === element) {
            return true
          }
        }
        return false
      }
    }
  })
}

const loadPollyfills = () => {
  nodeListPrototypes()
  nodePrototypes()
  elementMatchesPrototype()
}

export default loadPollyfills
