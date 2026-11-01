import js from "@eslint/js";
import globals from "globals";
import jsxA11y from "eslint-plugin-jsx-a11y";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["node_modules", "dist", "../web"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  jsxA11y.flatConfigs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: { globals: globals.browser },
    plugins: { "react-hooks": reactHooks },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      // A scrollable region must be keyboard focusable (WCAG 2.1.1), so tabIndex is allowed on role="region".
      "jsx-a11y/no-noninteractive-tabindex": ["error", { roles: ["region"] }],
      eqeqeq: "error",
      "no-console": "error",
    },
  },
);
