module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: [
    'plugin:vue/essential',
    '@vue/airbnb',
  ],
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'semi': ["error", "never"],
    'func-style': ["error", "expression"],
    'comma-dangle': ["error", "never"],
    'indent': ["error", 2],
    'no-tabs': 'off',
    'no-multiple-empty-lines': ["error", { "max": 1 }],
    'import/extensions': 'off',
    'import/no-mutable-exports': 'off',
    'import/no-unresolved': 'off',
    'no-param-reassign': 'off',
    'camelcase': 'off',
    'no-continue': 'off',
    'max-len': 'off',
    'no-unused-expressions': 'off',
    'arrow-parens': 'off',
    'no-alert': 'off',
    'consistent-return': 'off',
    'radix': 'off',
    'no-prototype-builtins': 'off',
    'no-restricted-syntax': 'off',
    'no-restricted-globals': 'off',
    'no-nested-ternary': 'off',
    'no-await-in-loop': 'off',
    'guard-for-in': 'off',
    'dot-notation': 'off',
    'no-underscore-dangle': 'off',
    'object-curly-newline': 'off',
    'import/prefer-default-export': 'off',
    'import/first': 'off',
    'quote-props': 'off',
    'vue/no-use-v-if-with-v-for': ['error', {
    'allowUsingIterationVar': true
    }],
    'vue/no-side-effects-in-computed-properties': 'off'
  },
  parserOptions: {
    parser: 'babel-eslint',
  },
};
