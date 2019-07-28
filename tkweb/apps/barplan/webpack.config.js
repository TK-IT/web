const path = require("path");

const HtmlWebpackPlugin = require("html-webpack-plugin");

module.exports = {
	entry: "./src/index.tsx",
	resolve: {
		extensions: [".ts", ".tsx", ".js"]
	},
	output: {
		path: path.join(__dirname, "/dist"),
		filename: "barplan.min.js"
	},
	module: {
		rules: [
			{
				test: /\.tsx?$/,
				use: {
					loader: "ts-loader"
				}
			},
			{
				test: /\.txt$/,
				use: {
					loader: "raw-loader"
				}
			},
			{
				test: /\.scss$/,
				use: [
					{
						loader: "style-loader" // creates style nodes from JS strings
					},
					{
						loader: "css-loader",
						query: {
							modules: true,
							sourceMap: true,
							localIdentName: "[name]_[local]"
							// localIdentName: "[name]__[local]___[hash:base64:5]"
						}
					},
					{
						loader: "sass-loader" //</span> compiles Sass to CSS
					}
				]
			}
		]
	},
	plugins: [
		new HtmlWebpackPlugin({
			template: "./src/index.html"
		})
	]
}
