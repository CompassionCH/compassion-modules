import React from 'react';

export default class extends React.Component {
    render() {
        let styles = {
            loadingContainer: {
                display: 'table-cell',
                verticalAlign: 'middle',
                height: '80vh',
            },
            loadingTextContainer: {
                width: '98vw',
                textAlign: 'center',
                paddingTop: 10
            },
        };

        return (
            <div style={styles.loadingContainer}>
                <div style={styles.loadingTextContainer} dangerouslySetInnerHTML={{__html: this.props.text}}/>
            </div>
        )
    }
}