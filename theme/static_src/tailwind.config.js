/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

module.exports = {
    content: [
        /**
         * HTML. Paths to Django template files that will contain Tailwind CSS classes.
         */

        /*  Templates within theme app (<tailwInd_app_name>/templates), e.g. base.html. */
        '../templates/**/*.html',

        /*
         * Main templates directory of the project (BASE_DIR/templates).
         * Adjust the following line to match your project structure.
         */
        '../../templates/**/*.html',

        /*
         * Templates in other django apps (BASE_DIR/<any_app_name>/templates).
         * Adjust the following line to match your project structure.
         */
        '../../**/templates/**/*.html',
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#6366F1', // indigo-500
                    dark: '#4F46E5',    // indigo-600
                },
                secondary: {
                    DEFAULT: '#D946EF', // fuchsia-500
                },
                dark: '#09090B',      // nearly black, used in portfolio
            },
            fontFamily: {
                sans: ['"Inter"', 'system-ui', 'sans-serif'],
                display: ['"Poppins"', 'sans-serif'],
            },
            borderRadius: {
                'pill': '9999px',
            },
            animation: {
                'sakura-fall': 'sakura-fall linear infinite',
                'sakura-sway': 'sakura-sway ease-in-out infinite',
                'fade-in-up': 'fade-in-up 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
                'fade-in': 'fade-in 0.6s ease-out forwards',
                'float': 'float 6s ease-in-out infinite',
            },
            keyframes: {
                'sakura-fall': {
                    '0%':   { transform: 'translateY(-10vh) rotate(0deg)', opacity: '0' },
                    '10%':  { opacity: '1' },
                    '90%':  { opacity: '1' },
                    '100%': { transform: 'translateY(110vh) rotate(720deg)', opacity: '0' },
                },
                'sakura-sway': {
                    '0%, 100%': { transform: 'translateX(0px)' },
                    '50%':      { transform: 'translateX(80px)' },
                },
                'fade-in-up': {
                    '0%':   { opacity: '0', transform: 'translateY(30px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                'fade-in': {
                    '0%':   { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%':      { transform: 'translateY(-20px)' },
                },
            },
        },
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
    ],
}
