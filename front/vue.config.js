module.exports = {
    outputDir: 'dist',
    devServer: { /* webpack options go here */
        watchOptions: {
            ignored: /node_modules/
        }
    }
}
